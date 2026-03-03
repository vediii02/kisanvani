import React, { useEffect, useState } from "react";
import api from "@/api/api";
import { useAuth } from "@/contexts/AuthContext";
import {
  Package,
  Plus,
  Upload,
  Trash2,
  Download,
  Edit2,
  X,
  Search,
} from "lucide-react";
import { toast } from "sonner";

// Category and Sub-category mapping
const CATEGORY_OPTIONS = {
  Pesticide: [
    "Insecticide",
    "Fungicide",
    "Herbicide",
    "Nematicide",
    "Acaricide",
    "Molluscicide",
  ],
  Fertilizer: [
    "NPK",
    "Organic",
    "Micronutrient",
    "Liquid Fertilizer",
    "Foliar Spray",
    "Biofertilizer",
  ],
  Seed: [
    "Hybrid",
    "Open Pollinated",
    "GMO",
    "Certified Seed",
    "Indigenous Variety",
  ],
  Equipment: [
    "Sprayer",
    "Drip Irrigation",
    "Mulcher",
    "Harvester",
    "Seeder",
    "Others",
  ],
  "Growth Regulator": [
    "Plant Hormone",
    "Nutrient Booster",
    "Root Promoter",
    "Stress Relief",
    "Yield Enhancer",
  ],
  Bioproduct: [
    "Bioinsecticide",
    "Biofungicide",
    "Bio-Nematicide",
    "Biofertilizer",
    "Bio-Stimulant",
  ],
  Other: ["General", "Miscellaneous"],
};

export default function CompanyProductsPage() {
  const { user } = useAuth();
  const [products, setProducts] = useState([]);
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [showBulkUploadModal, setShowBulkUploadModal] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [editingProduct, setEditingProduct] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterBrand, setFilterBrand] = useState("all");
  const [filterCategory, setFilterCategory] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [formData, setFormData] = useState({
    brand_id: "",
    name: "",
    category: "",
    sub_category: "",
    description: "",
    target_crops: "",
    target_problems: "",
    dosage: "",
    usage_instructions: "",
    safety_precautions: "",
    price_range: "",
    is_active: true,
  });

  const companyId = user?.company_id || (() => {
    try {
      const token = localStorage.getItem('token');
      if (token) {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.company_id;
      }
    } catch (e) {
      console.error('Error parsing token:', e);
    }
    return null;
  })();

  // Debug logging
  console.log("🔍 CompanyProductsPage - User:", user);
  console.log("🔍 CompanyProductsPage - Company ID:", companyId);

  useEffect(() => {
    if (!companyId) return;
    fetchData();
  }, [companyId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      console.log("🔄 Fetching products with company_id:", companyId);
      console.log("🔄 User object:", user);

      const [productsRes, brandsRes] = await Promise.all([
        api.get(`/company/products`),
        api.get("/company/brands"),
      ]);

      console.log("✅ Products fetched:", productsRes.data);
      console.log("✅ Brands fetched:", brandsRes.data);

      setProducts(productsRes.data || []);
      setBrands(brandsRes.data || []);
    } catch (err) {
      console.error("❌ Fetch Error:", err);
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const dataToSend = {
        ...formData,
        brand_id: formData.brand_id ? parseInt(formData.brand_id) : null,
        company_id: companyId,
      };
      await api.post(`/company/products`, dataToSend);
      toast.success("Product created successfully");
      await fetchData();
      resetForm();
      setShowModal(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to create product");
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      const dataToSend = {
        ...formData,
        brand_id: formData.brand_id ? parseInt(formData.brand_id) : null,
      };
      await api.put(`/company/products/${editingProduct.id}`, dataToSend);
      toast.success("Product updated successfully");
      await fetchData();
      resetForm();
      setEditingProduct(null);
      setShowModal(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to update product");
    }
  };

  const handleBulkUpload = async (e) => {
    if (!selectedFile) {
      toast.error("Please select a file first");
      return;
    }

    try {
      setUploading(true);
      const formDataFile = new FormData();
      formDataFile.append("file", selectedFile);

      // Ensure we have a valid company_id with fallback
      const targetCompanyId = companyId || user?.company_id || (() => {
        try {
          const token = localStorage.getItem('token');
          if (token) {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.company_id;
          }
        } catch (e) {
          console.error('Error parsing token:', e);
        }
        return null;
      })();

      if (!targetCompanyId) {
        toast.error("Company ID not found. Please log in again.");
        return;
      }

      formDataFile.append("company_id", targetCompanyId.toString());

      console.log("📤 Uploading file...", {
        fileName: selectedFile.name,
        companyId: targetCompanyId,
        user: user
      });

      const uploadRes = await api.post(
        "/company/products/bulk-upload",
        formDataFile,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        },
      );

      console.log("✅ Upload Response:", uploadRes.data);
      setUploadResult(uploadRes.data);

      const hasErrors = uploadRes.data?.error_count > 0 || uploadRes.data?.errors?.length > 0;

      if (hasErrors) {
        toast.warning(
          `Imported: ${uploadRes.data?.success_count || 0}. Exists/Failed: ${uploadRes.data?.error_count || 0}`,
          { duration: 5000 }
        );
      } else {
        toast.success(
          `Products uploaded successfully! Imported: ${uploadRes.data?.success_count || 0}`,
        );
        setTimeout(() => {
          setShowBulkUploadModal(false);
          setSelectedFile(null);
          setUploadResult(null);
        }, 1500);
      }

      setTimeout(() => {
        console.log("🔄 Reloading products...");
        fetchData();
      }, 500);

      if (document.getElementById("file-input")) {
        document.getElementById("file-input").value = "";
      }
    } catch (err) {
      console.error("❌ Upload Error:", err);
      const errorMsg =
        typeof err.response?.data?.detail === "string"
          ? err.response?.data?.detail
          : err.response?.data?.message || "Bulk upload failed";
      toast.error(errorMsg);
    } finally {
      setUploading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      toast.success(`File selected: ${file.name}`);
    }
  };

  const handleDelete = async (productId) => {
    if (window.confirm("Are you sure you want to delete this product?")) {
      try {
        await api.delete(`/company/products/${productId}`);
        toast.success("Product deleted successfully");
        await fetchData();
      } catch (err) {
        toast.error(err.response?.data?.detail || "Failed to delete product");
      }
    }
  };

  const resetForm = () => {
    setFormData({
      brand_id: "",
      name: "",
      category: "",
      sub_category: "",
      description: "",
      target_crops: "",
      target_problems: "",
      dosage: "",
      usage_instructions: "",
      safety_precautions: "",
      price_range: "",
      is_active: true,
    });
  };

  const openEditModal = (product) => {
    setEditingProduct(product);
    setFormData({
      brand_id: product.brand_id || "",
      name: product.name || "",
      category: product.category || "",
      sub_category: product.sub_category || "",
      description: product.description || "",
      target_crops: product.target_crops || "",
      target_problems: product.target_problems || "",
      dosage: product.dosage || "",
      usage_instructions: product.usage_instructions || "",
      safety_precautions: product.safety_precautions || "",
      price_range: product.price_range || "",
      is_active: product.is_active !== undefined ? product.is_active : true,
    });
    setShowModal(true);
  };

  const downloadTemplate = () => {
    const headers = [
      "name",
      "category",
      "brand_name",
      "sub_category",
      "description",
      "target_crops",
      "target_problems",
      "dosage",
      "price_range",
      "usage_instructions",
      "safety_precautions",
      "is_active",
    ];

    const exampleRow = [
      "Organic Neem Oil",
      "Pesticide",
      "Brand 1",
      "Natural Pest Control",
      "Pure neem oil for organic farming",
      "Wheat;Rice;Corn",
      "Insects;Mites",
      "2-3ml per liter water",
      "400-500",
      "Dilute 2-3ml in 1 liter water and spray",
      "Use gloves and mask; Keep away from children",
      "true",
    ];

    const headerLine = headers.join(",");
    const exampleLine = exampleRow.map((val) => `"${val}"`).join(",");
    const csv = [headerLine, exampleLine].join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "products_template.csv";
    a.click();
  };

  if (loading)
    return <div className="text-center py-8">Loading products...</div>;

  // Get unique categories and brands for filters
  const uniqueCategories = Array.from(
    new Set(products.map((p) => p.category)),
  ).filter(Boolean);
  const uniqueBrands = brands.filter((b) =>
    products.some((p) => p.brand_id === b.id),
  );

  // Filter products based on search and filters
  const filteredProducts = products.filter((product) => {
    const matchesSearch =
      (product.name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (product.category || "").toLowerCase().includes(searchTerm.toLowerCase());
    const matchesBrand =
      filterBrand === "all" || product.brand_id === parseInt(filterBrand);
    const matchesCategory =
      filterCategory === "all" || product.category === filterCategory;
    const matchesStatus =
      filterStatus === "all" ||
      (filterStatus === "active" && product.is_active) ||
      (filterStatus === "inactive" && !product.is_active);

    return matchesSearch && matchesBrand && matchesCategory && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Products Management
        </h1>
        <p className="text-gray-600 mt-1">
          Manage your company's products
        </p>
      </div>

      {/* Top Buttons */}
      <div className="flex gap-3 justify-end">
        <button
          onClick={() => setShowBulkUploadModal(true)}
          className="flex items-center gap-2 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 shadow-md font-semibold transition-all"
        >
          <Upload className="h-5 w-5" />
          Bulk Upload
        </button>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 shadow-md font-semibold transition-all"
        >
          <Plus className="h-5 w-5" />
          Add Product
        </button>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow p-4 space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search products..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>

        <div className="grid grid-cols-3 gap-4">
          <select
            value={filterBrand}
            onChange={(e) => setFilterBrand(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            <option value="all">All Brands</option>
            {uniqueBrands.map((brand) => (
              <option key={brand.id} value={brand.id}>
                {brand.name}
              </option>
            ))}
          </select>

          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            <option value="all">All Categories</option>
            {uniqueCategories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      {/* Products Table */}
      {filteredProducts.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center min-h-96 flex flex-col items-center justify-center">
          <Package className="h-24 w-24 text-gray-400 mx-auto mb-4" />
          <h3 className="text-2xl font-semibold text-gray-900 mb-2">
            No Products Found
          </h3>
          <p className="text-gray-600">
            Get started by adding your first product
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                  Product
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                  Brand
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                  Target Crops
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredProducts.map((product) => {
                const brand = brands.find((b) => b.id === product.brand_id);
                return (
                  <tr key={product.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {product.name}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {product.category}
                      {product.sub_category ? ` / ${product.sub_category}` : ""}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {product.brand_name || "-"}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {product.target_crops || "-"}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${product.is_active
                          ? "bg-green-100 text-green-800"
                          : "bg-gray-100 text-gray-800"
                          }`}
                      >
                        {product.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm flex gap-2">
                      <button
                        onClick={() => openEditModal(product)}
                        className="text-blue-600 hover:text-blue-900 hover:bg-blue-50 px-3 py-1 rounded"
                        title="Edit"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(product.id)}
                        className="text-red-600 hover:text-red-900 hover:bg-red-50 px-3 py-1 rounded"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Create/Edit Product Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full my-8">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">
                {editingProduct ? "Edit Product" : "Add Product"}
              </h2>
              <button
                onClick={() => {
                  setShowModal(false);
                  setEditingProduct(null);
                  resetForm();
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            <form
              onSubmit={editingProduct ? handleUpdate : handleCreate}
              className="p-6 space-y-4 max-h-96 overflow-y-auto"
            >
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Brand *
                  </label>
                  <select
                    value={formData.brand_id}
                    onChange={(e) =>
                      setFormData({ ...formData, brand_id: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    required
                  >
                    <option value="">Select Brand</option>
                    {brands.map((brand) => (
                      <option key={brand.id} value={brand.id}>
                        {brand.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Product Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) =>
                      setFormData({ ...formData, name: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Category *
                  </label>
                  <select
                    value={formData.category}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        category: e.target.value,
                        sub_category: "",
                      })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    required
                  >
                    <option value="">Select Category</option>
                    {Object.keys(CATEGORY_OPTIONS).map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Sub Category *
                  </label>
                  <select
                    value={formData.sub_category}
                    onChange={(e) =>
                      setFormData({ ...formData, sub_category: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    disabled={!formData.category}
                    required
                  >
                    <option value="">Select Sub Category</option>
                    {formData.category &&
                      CATEGORY_OPTIONS[formData.category]?.map((sub) => (
                        <option key={sub} value={sub}>
                          {sub}
                        </option>
                      ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Target Crops
                  </label>
                  <input
                    type="text"
                    value={formData.target_crops}
                    onChange={(e) =>
                      setFormData({ ...formData, target_crops: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="e.g., Wheat, Corn, Rice"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Target Problems
                  </label>
                  <input
                    type="text"
                    value={formData.target_problems}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        target_problems: e.target.value,
                      })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="e.g., Leaf spot, Rust"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Dosage
                  </label>
                  <input
                    type="text"
                    value={formData.dosage}
                    onChange={(e) =>
                      setFormData({ ...formData, dosage: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="e.g., 500ml per acre"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Price Range
                  </label>
                  <input
                    type="text"
                    value={formData.price_range}
                    onChange={(e) =>
                      setFormData({ ...formData, price_range: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="e.g., $10-$20 per unit"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  rows={2}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Usage Instructions
                </label>
                <textarea
                  value={formData.usage_instructions}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      usage_instructions: e.target.value,
                    })
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  rows={2}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Safety Precautions
                </label>
                <textarea
                  value={formData.safety_precautions}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      safety_precautions: e.target.value,
                    })
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  rows={2}
                />
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) =>
                    setFormData({ ...formData, is_active: e.target.checked })
                  }
                  className="rounded"
                />
                <label
                  htmlFor="is_active"
                  className="text-sm font-medium text-gray-700"
                >
                  Active
                </label>
              </div>

              <div className="flex gap-2 pt-6 border-t">
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium"
                >
                  {editingProduct ? "Update Product" : "Add Product"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false);
                    setEditingProduct(null);
                    resetForm();
                  }}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-medium"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Bulk Upload Modal */}
      {showBulkUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900">
                Bulk Upload Products
              </h2>
              <p className="text-gray-600 text-sm mt-1">
                Upload a CSV file with your products
              </p>
            </div>

            <div className="p-6 space-y-4">
              <div className="border-2 border-dashed border-gray-300 bg-gray-50 rounded-lg p-6 text-center hover:border-blue-400 transition-colors cursor-pointer">
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileSelect}
                  disabled={uploading}
                  className="hidden"
                  id="file-input"
                />
                <label htmlFor="file-input" className="cursor-pointer block">
                  <Upload className="h-12 w-12 text-blue-600 mx-auto mb-2" />
                  <p className="text-sm font-medium text-gray-900">
                    {selectedFile
                      ? `Selected: ${selectedFile.name}`
                      : "Click to select CSV file"}
                  </p>
                  <p className="text-xs text-gray-600">or drag and drop</p>
                </label>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-xs text-blue-900">
                  <strong>Required Columns:</strong> name, category
                </p>
                <p className="text-xs text-blue-800 mt-2">
                  <strong>Optional:</strong> brand_name, sub_category,
                  description, dosage, target_crops, is_active
                </p>
              </div>

              {/* Upload Result */}
              {uploadResult && (
                <div className={`p-4 rounded-lg mt-4 ${uploadResult.success_count > 0 ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'}`}>
                  <h3 className="font-semibold text-gray-900 mb-2">Upload Results:</h3>
                  <div className="space-y-1 text-sm">
                    <p className="text-green-700">✅ Imported: {uploadResult.success_count} products</p>
                    <p className="text-red-700">❌ Failed/Skipped: {uploadResult.error_count}</p>
                  </div>
                  {uploadResult.errors && uploadResult.errors.length > 0 && (
                    <div className="mt-3 max-h-32 overflow-y-auto bg-white p-2 border border-red-100 rounded">
                      <p className="text-xs font-semibold text-red-800 mb-1">Errors:</p>
                      {uploadResult.errors.map((err, idx) => (
                        <p key={idx} className="text-xs text-red-700">
                          {err}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <button
                onClick={downloadTemplate}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium"
              >
                <Download className="h-4 w-4" />
                Download Template
              </button>

              <button
                onClick={() => document.getElementById("file-input").click()}
                disabled={uploading}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Upload className="h-4 w-4" />
                {uploading ? "Uploading..." : "Select File"}
              </button>

              <button
                onClick={handleBulkUpload}
                disabled={uploading || !selectedFile}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Upload className="h-4 w-4" />
                {uploading ? "Uploading..." : "Upload"}
              </button>

              <button
                onClick={() => {
                  setShowBulkUploadModal(false);
                  setSelectedFile(null);
                  setUploadResult(null);
                }}
                disabled={uploading}
                className="w-full px-4 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium disabled:opacity-50 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
