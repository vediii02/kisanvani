// // Platform-wide Product Safety Control - Banned Products Management
// import React, { useState, useEffect } from 'react';
// import {
//   Shield,
//   AlertTriangle,
//   Plus,
//   Trash2,
//   Calendar,
//   FileText,
//   Search
// } from 'lucide-react';
// import api from '../api/api';

// const ProductSafetyControl = () => {
//   const [bannedProducts, setBannedProducts] = useState([]);
//   const [loading, setLoading] = useState(true);
//   const [showAddModal, setShowAddModal] = useState(false);
//   const [newBan, setNewBan] = useState({
//     product_name: '',
//     chemical_name: '',
//     ban_reason: '',
//     regulatory_reference: '',
//     expiry_date: null
//   });

//   useEffect(() => {
//     fetchBannedProducts();
//   }, []);

//   const fetchBannedProducts = async () => {
//     try {
//       setLoading(true);
//       const response = await api.get('/superadmin/banned-products');
//       setBannedProducts(response.data);
//     } catch (error) {
//       console.error('Error fetching banned products:', error);
//     } finally {
//       setLoading(false);
//     }
//   };

//   const handleAddBan = async (e) => {
//     e.preventDefault();
    
//     if (!newBan.product_name || !newBan.ban_reason) {
//       alert('Product name and ban reason are required');
//       return;
//     }

//     try {
//       await api.post('/superadmin/banned-products', newBan);
//       alert('✅ Product banned globally!\n\nAI will no longer suggest this product to any organisation.');
//       setShowAddModal(false);
//       setNewBan({
//         product_name: '',
//         chemical_name: '',
//         ban_reason: '',
//         regulatory_reference: '',
//         expiry_date: null
//       });
//       fetchBannedProducts();
//     } catch (error) {
//       console.error('Error banning product:', error);
//       alert('Failed to ban product');
//     }
//   };

//   return (
//     <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
//       {/* Header */}
//       <div className="flex justify-between items-start">
//         <div className="flex items-center gap-4">
//           <div className="p-3 bg-gradient-to-br from-red-500 to-red-700 rounded-xl shadow-lg">
//             <Shield className="h-8 w-8 text-white" />
//           </div>
//           <div>
//             <h1 className="text-3xl font-bold text-gray-900">Product Safety Control</h1>
//             <p className="text-gray-600 mt-1">Global ban list - AI will never suggest these products</p>
//           </div>
//         </div>
        
//         <button
//           onClick={() => setShowAddModal(true)}
//           className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 shadow-lg transition-all"
//         >
//           <Plus className="h-5 w-5" />
//           Ban Product Globally
//         </button>
//       </div>

//       {/* Warning Banner */}
//       <div className="bg-red-50 border-l-4 border-red-500 rounded-lg p-6">
//         <div className="flex items-start gap-3">
//           <AlertTriangle className="h-6 w-6 text-red-600 mt-1" />
//           <div>
//             <h3 className="text-red-800 font-bold text-lg mb-2">🚨 CRITICAL SAFETY CONTROL</h3>
//             <p className="text-red-700 mb-2">
//               Products banned here are <span className="font-bold">BLOCKED PLATFORM-WIDE</span>. 
//               AI will never suggest them to any organisation, regardless of their own product catalog.
//             </p>
//             <p className="text-red-700">
//               Use only for: ❌ Banned pesticides/chemicals | ⚠️ Safety concerns | 📜 Regulatory violations
//             </p>
//           </div>
//         </div>
//       </div>

//       {/* Stats */}
//       <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
//         <div className="bg-white rounded-lg shadow p-4">
//           <div className="flex items-center justify-between">
//             <div>
//               <p className="text-gray-600 text-sm">Total Banned</p>
//               <p className="text-3xl font-bold text-red-600">{bannedProducts.length}</p>
//             </div>
//             <Shield className="h-10 w-10 text-red-500" />
//           </div>
//         </div>
        
//         <div className="bg-white rounded-lg shadow p-4">
//           <div className="flex items-center justify-between">
//             <div>
//               <p className="text-gray-600 text-sm">Active Bans</p>
//               <p className="text-3xl font-bold text-red-600">
//                 {bannedProducts.filter(b => b.is_active).length}
//               </p>
//             </div>
//             <AlertTriangle className="h-10 w-10 text-red-500" />
//           </div>
//         </div>

//         <div className="bg-white rounded-lg shadow p-4">
//           <div className="flex items-center justify-between">
//             <div>
//               <p className="text-gray-600 text-sm">Expiring Soon</p>
//               <p className="text-3xl font-bold text-yellow-600">
//                 {bannedProducts.filter(b => {
//                   if (!b.expiry_date) return false;
//                   const expiry = new Date(b.expiry_date);
//                   const today = new Date();
//                   const diffDays = (expiry - today) / (1000 * 60 * 60 * 24);
//                   return diffDays > 0 && diffDays <= 30;
//                 }).length}
//               </p>
//             </div>
//             <Calendar className="h-10 w-10 text-yellow-500" />
//           </div>
//         </div>
//       </div>

//       {/* Banned Products Table */}
//       <div className="bg-white rounded-xl shadow-lg overflow-hidden">
//         {loading ? (
//           <div className="flex items-center justify-center p-12">
//             <div className="text-center">
//               <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-red-600 mx-auto"></div>
//               <p className="mt-4 text-gray-600">Loading banned products...</p>
//             </div>
//           </div>
//         ) : bannedProducts.length === 0 ? (
//           <div className="p-12 text-center">
//             <Shield className="h-16 w-16 text-gray-300 mx-auto mb-4" />
//             <p className="text-gray-600 text-lg">No banned products</p>
//             <p className="text-gray-500 text-sm mt-2">Platform-wide product bans will appear here</p>
//           </div>
//         ) : (
//           <table className="min-w-full divide-y divide-gray-200">
//             <thead className="bg-red-50">
//               <tr>
//                 <th className="px-6 py-4 text-left text-xs font-medium text-red-700 uppercase">Product</th>
//                 <th className="px-6 py-4 text-left text-xs font-medium text-red-700 uppercase">Ban Reason</th>
//                 <th className="px-6 py-4 text-left text-xs font-medium text-red-700 uppercase">Regulatory Ref</th>
//                 <th className="px-6 py-4 text-center text-xs font-medium text-red-700 uppercase">Banned Date</th>
//                 <th className="px-6 py-4 text-center text-xs font-medium text-red-700 uppercase">Expiry</th>
//                 <th className="px-6 py-4 text-center text-xs font-medium text-red-700 uppercase">Status</th>
//               </tr>
//             </thead>
//             <tbody className="bg-white divide-y divide-gray-200">
//               {bannedProducts.map((ban) => (
//                 <tr key={ban.id} className={`${ban.is_active ? 'bg-red-50' : 'bg-gray-50'}`}>
//                   <td className="px-6 py-4">
//                     <div className="flex items-center gap-2">
//                       <AlertTriangle className={`h-5 w-5 ${ban.is_active ? 'text-red-600' : 'text-gray-400'}`} />
//                       <div>
//                         <div className="font-bold text-gray-900">{ban.product_name}</div>
//                         {ban.chemical_name && (
//                           <div className="text-xs text-gray-500">{ban.chemical_name}</div>
//                         )}
//                       </div>
//                     </div>
//                   </td>
                  
//                   <td className="px-6 py-4">
//                     <div className="text-sm text-gray-900">{ban.ban_reason}</div>
//                   </td>
                  
//                   <td className="px-6 py-4">
//                     <div className="text-sm text-gray-600">{ban.regulatory_reference || 'N/A'}</div>
//                   </td>
                  
//                   <td className="px-6 py-4 text-center">
//                     <div className="text-sm text-gray-900">
//                       {new Date(ban.banned_at).toLocaleDateString()}
//                     </div>
//                   </td>
                  
//                   <td className="px-6 py-4 text-center">
//                     {ban.expiry_date ? (
//                       <div className="text-sm text-gray-900">
//                         {new Date(ban.expiry_date).toLocaleDateString()}
//                       </div>
//                     ) : (
//                       <span className="text-gray-500 text-sm">Permanent</span>
//                     )}
//                   </td>
                  
//                   <td className="px-6 py-4 text-center">
//                     {ban.is_active ? (
//                       <span className="px-3 py-1 bg-red-100 text-red-800 text-xs font-bold rounded-full">
//                         🚫 BANNED
//                       </span>
//                     ) : (
//                       <span className="px-3 py-1 bg-gray-100 text-gray-800 text-xs font-semibold rounded-full">
//                         Inactive
//                       </span>
//                     )}
//                   </td>
//                 </tr>
//               ))}
//             </tbody>
//           </table>
//         )}
//       </div>

//       {/* Add Ban Modal */}
//       {showAddModal && (
//         <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
//           <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full mx-4">
//             <div className="bg-red-600 text-white px-6 py-4 rounded-t-xl flex items-center justify-between">
//               <div className="flex items-center gap-3">
//                 <Shield className="h-6 w-6" />
//                 <h2 className="text-xl font-bold">Ban Product Globally</h2>
//               </div>
//               <button
//                 onClick={() => setShowAddModal(false)}
//                 className="text-white hover:bg-red-700 rounded p-1"
//               >
//                 ✕
//               </button>
//             </div>
            
//             <form onSubmit={handleAddBan} className="p-6 space-y-4">
//               <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded mb-4">
//                 <p className="text-red-800 text-sm font-semibold">
//                   ⚠️ This will block the product across ALL organisations. AI will never suggest it.
//                 </p>
//               </div>

//               <div>
//                 <label className="block text-sm font-medium text-gray-700 mb-2">
//                   Product Name <span className="text-red-600">*</span>
//                 </label>
//                 <input
//                   type="text"
//                   value={newBan.product_name}
//                   onChange={(e) => setNewBan({ ...newBan, product_name: e.target.value })}
//                   className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
//                   placeholder="e.g., DDT, Monocrotophos"
//                   required
//                 />
//               </div>

//               <div>
//                 <label className="block text-sm font-medium text-gray-700 mb-2">
//                   Chemical Name
//                 </label>
//                 <input
//                   type="text"
//                   value={newBan.chemical_name}
//                   onChange={(e) => setNewBan({ ...newBan, chemical_name: e.target.value })}
//                   className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
//                   placeholder="Scientific/chemical name"
//                 />
//               </div>

//               <div>
//                 <label className="block text-sm font-medium text-gray-700 mb-2">
//                   Ban Reason <span className="text-red-600">*</span>
//                 </label>
//                 <textarea
//                   value={newBan.ban_reason}
//                   onChange={(e) => setNewBan({ ...newBan, ban_reason: e.target.value })}
//                   className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
//                   rows={3}
//                   placeholder="Safety concern, regulatory violation, banned by government..."
//                   required
//                 />
//               </div>

//               <div>
//                 <label className="block text-sm font-medium text-gray-700 mb-2">
//                   Regulatory Reference
//                 </label>
//                 <input
//                   type="text"
//                   value={newBan.regulatory_reference}
//                   onChange={(e) => setNewBan({ ...newBan, regulatory_reference: e.target.value })}
//                   className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
//                   placeholder="e.g., Ministry of Agriculture Order No. 2024/123"
//                 />
//               </div>

//               <div>
//                 <label className="block text-sm font-medium text-gray-700 mb-2">
//                   Expiry Date (Optional)
//                 </label>
//                 <input
//                   type="date"
//                   value={newBan.expiry_date || ''}
//                   onChange={(e) => setNewBan({ ...newBan, expiry_date: e.target.value || null })}
//                   className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
//                 />
//                 <p className="text-xs text-gray-500 mt-1">Leave empty for permanent ban</p>
//               </div>

//               <div className="flex gap-3 pt-4">
//                 <button
//                   type="submit"
//                   className="flex-1 bg-red-600 text-white py-3 rounded-lg font-semibold hover:bg-red-700 transition-all"
//                 >
//                   🚫 Ban Product Globally
//                 </button>
//                 <button
//                   type="button"
//                   onClick={() => setShowAddModal(false)}
//                   className="flex-1 bg-gray-200 text-gray-700 py-3 rounded-lg font-semibold hover:bg-gray-300 transition-all"
//                 >
//                   Cancel
//                 </button>
//               </div>
//             </form>
//           </div>
//         </div>
//       )}
//     </div>
//   );
// };

// export default ProductSafetyControl;
