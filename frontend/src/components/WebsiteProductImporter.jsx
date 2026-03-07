// // Import Products from Website - Super Admin Tool
// import React, { useState } from 'react';
// import { Globe, Download, AlertCircle, CheckCircle, Loader, Package } from 'lucide-react';
// import api from '../api/api';

// const WebsiteProductImporter = ({ organisationId, onImportComplete }) => {
//   const [websiteUrl, setWebsiteUrl] = useState('');
//   const [loading, setLoading] = useState(false);
//   const [result, setResult] = useState(null);
//   const [error, setError] = useState(null);

//   const handleImport = async () => {
//     if (!websiteUrl) {
//       setError('Please enter a website URL');
//       return;
//     }

//     // Basic URL validation
//     try {
//       new URL(websiteUrl);
//     } catch {
//       setError('Please enter a valid URL (e.g., https://example.com)');
//       return;
//     }

//     setLoading(true);
//     setError(null);
//     setResult(null);

//     try {
//       const response = await api.post(
//         `/superadmin/organisations-platform/${organisationId}/import-from-website`,
//         {
//           website_url: websiteUrl,
//           auto_create_brand: true
//         }
//       );

//       setResult(response.data);
//       setWebsiteUrl('');
      
//       if (onImportComplete) {
//         onImportComplete(response.data);
//       }
//     } catch (err) {
//       setError(err.response?.data?.detail || 'Failed to import products from website');
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <div className="bg-white rounded-xl shadow-md p-6">
//       <div className="flex items-center gap-3 mb-4">
//         <Globe className="h-6 w-6 text-blue-600" />
//         <h3 className="text-xl font-bold text-gray-900">Import Products from Website</h3>
//       </div>

//       <p className="text-gray-600 text-sm mb-4">
//         Enter a company website URL to automatically scrape and import their products. 
//         The system will detect products and create them in the database.
//       </p>

//       {/* Input Form */}
//       <div className="space-y-4">
//         <div>
//           <label className="block text-sm font-medium text-gray-700 mb-2">
//             Website URL
//           </label>
//           <input
//             type="url"
//             value={websiteUrl}
//             onChange={(e) => setWebsiteUrl(e.target.value)}
//             placeholder="https://example.com/products"
//             className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
//             disabled={loading}
//           />
//           <p className="text-xs text-gray-500 mt-1">
//             💡 Tip: Use the products page URL for best results
//           </p>
//         </div>

//         <button
//           onClick={handleImport}
//           disabled={loading || !websiteUrl}
//           className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-all disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
//         >
//           {loading ? (
//             <>
//               <Loader className="h-5 w-5 animate-spin" />
//               Importing Products...
//             </>
//           ) : (
//             <>
//               <Download className="h-5 w-5" />
//               Import Products
//             </>
//           )}
//         </button>
//       </div>

//       {/* Error Message */}
//       {error && (
//         <div className="mt-4 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg flex items-start gap-3">
//           <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
//           <div>
//             <p className="text-red-800 font-medium">Import Failed</p>
//             <p className="text-red-700 text-sm mt-1">{error}</p>
//           </div>
//         </div>
//       )}

//       {/* Success Message */}
//       {result && (
//         <div className="mt-4 p-4 bg-green-50 border-l-4 border-green-500 rounded-lg">
//           <div className="flex items-start gap-3">
//             <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
//             <div className="flex-1">
//               <p className="text-green-800 font-medium">Import Successful! 🎉</p>
//               <div className="mt-2 space-y-1 text-sm text-green-700">
//                 <p>✓ Imported: <strong>{result.imported_count}</strong> products</p>
//                 <p>↺ Skipped (already exist): <strong>{result.skipped_count}</strong> products</p>
//                 <p>🔍 Total found on website: <strong>{result.total_found}</strong> products</p>
//                 {result.imported_count > 0 && (
//                   <p className="mt-2 text-green-800">
//                     Products have been added to Brand ID: <strong>{result.brand_id}</strong>
//                   </p>
//                 )}
//               </div>
//             </div>
//           </div>
//         </div>
//       )}

//       {/* How it works */}
//       <div className="mt-6 p-4 bg-blue-50 border-l-4 border-blue-500 rounded-lg">
//         <div className="flex items-start gap-3">
//           <Package className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
//           <div className="text-sm text-blue-800">
//             <p className="font-semibold mb-2">How it works:</p>
//             <ol className="list-decimal list-inside space-y-1">
//               <li>System visits the website URL</li>
//               <li>Automatically detects product listings</li>
//               <li>Extracts product names and descriptions</li>
//               <li>Creates/updates brand automatically</li>
//               <li>Imports products (skips duplicates)</li>
//             </ol>
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default WebsiteProductImporter;
