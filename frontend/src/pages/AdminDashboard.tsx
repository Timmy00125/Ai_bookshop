import React, { useState, useEffect } from 'react';
import api from '../api';
import { Shield, BookOpen, Plus, Trash2, RefreshCw } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Navigate } from 'react-router-dom';

export default function AdminDashboard() {
  const { user } = useAuth();
  const [books, setBooks] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [addingBook, setAddingBook] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  
  // New book state
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [price, setPrice] = useState('');
  const [genre, setGenre] = useState('');
  const [description, setDescription] = useState('');
  const [coverUrl, setCoverUrl] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [booksRes, ordersRes] = await Promise.all([
        api.get('/books/'),
        api.get('/orders/all')
      ]);
      setBooks(booksRes.data);
      setOrders(ordersRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddBook = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddingBook(true);
    try {
      await api.post('/books/', {
        title, author, price: parseFloat(price), genre, description, cover_image_url: coverUrl
      });
      // Reset form
      setTitle(''); setAuthor(''); setPrice(''); setGenre(''); setDescription(''); setCoverUrl('');
      await fetchData();
    } catch (err) {
      console.error(err);
      alert('Failed to add book');
    } finally {
      setAddingBook(false);
    }
  };

  const handleDeleteBook = async (id: number) => {
    if(!window.confirm("Are you sure you want to delete this book?")) return;
    try {
      await api.delete(`/books/${id}`);
      await fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleReindex = async () => {
    setReindexing(true);
    try {
      await api.post('/ai/reindex');
      alert("Search re-indexed successfully!");
    } catch (err) {
      console.error(err);
      alert("Failed to re-index");
    } finally {
      setReindexing(false);
    }
  };

  if (user?.role !== 'admin') {
    return <Navigate to="/" />;
  }

  if (loading) {
     return (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      );
  }

  const totalRevenue = orders.reduce((acc, order) => acc + parseFloat(order.total_price), 0);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-12">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3">
          <Shield size={32} className="text-indigo-600" /> Admin Dashboard
        </h1>
        <button 
          onClick={handleReindex}
          disabled={reindexing}
          className="bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold py-2.5 px-5 rounded-xl transition flex items-center gap-2 border border-indigo-200"
        >
          <RefreshCw size={18} className={reindexing ? "animate-spin" : ""} />
          {reindexing ? 'Reindexing...' : 'Reindex Search Vectors'}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
         <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
            <h3 className="text-slate-500 font-bold uppercase tracking-wider text-xs mb-2">Total Books</h3>
            <div className="text-4xl font-extrabold text-slate-900">{books.length}</div>
         </div>
         <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
            <h3 className="text-slate-500 font-bold uppercase tracking-wider text-xs mb-2">Total Orders</h3>
            <div className="text-4xl font-extrabold text-slate-900">{orders.length}</div>
         </div>
         <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
            <h3 className="text-slate-500 font-bold uppercase tracking-wider text-xs mb-2">Total Revenue</h3>
            <div className="text-4xl font-extrabold text-emerald-600">${totalRevenue.toFixed(2)}</div>
         </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
         <div className="lg:col-span-1">
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 sticky top-24">
               <h3 className="text-xl font-extrabold text-slate-900 mb-6 flex items-center gap-2">
                 <Plus size={24} className="text-indigo-600" /> Add New Book
               </h3>
               <form onSubmit={handleAddBook} className="space-y-4">
                 <div>
                   <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Title</label>
                   <input required type="text" value={title} onChange={e => setTitle(e.target.value)} className="w-full px-4 py-2 bg-slate-50 rounded-lg border border-slate-200 focus:bg-white focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition" />
                 </div>
                 <div>
                   <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Author</label>
                   <input required type="text" value={author} onChange={e => setAuthor(e.target.value)} className="w-full px-4 py-2 bg-slate-50 rounded-lg border border-slate-200 focus:bg-white focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition" />
                 </div>
                 <div className="grid grid-cols-2 gap-4">
                   <div>
                     <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Price ($)</label>
                     <input required type="number" step="0.01" value={price} onChange={e => setPrice(e.target.value)} className="w-full px-4 py-2 bg-slate-50 rounded-lg border border-slate-200 focus:bg-white focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition" />
                   </div>
                   <div>
                     <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Genre</label>
                     <input type="text" value={genre} onChange={e => setGenre(e.target.value)} className="w-full px-4 py-2 bg-slate-50 rounded-lg border border-slate-200 focus:bg-white focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition" />
                   </div>
                 </div>
                 <div>
                   <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Cover Image URL</label>
                   <input type="text" value={coverUrl} onChange={e => setCoverUrl(e.target.value)} className="w-full px-4 py-2 bg-slate-50 rounded-lg border border-slate-200 focus:bg-white focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition" />
                 </div>
                 <div>
                   <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Description</label>
                   <textarea rows={4} value={description} onChange={e => setDescription(e.target.value)} className="w-full px-4 py-2 bg-slate-50 rounded-lg border border-slate-200 focus:bg-white focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition"></textarea>
                 </div>
                 <button type="submit" disabled={addingBook} className="w-full bg-indigo-600 text-white font-bold py-3 rounded-xl hover:bg-indigo-700 transition disabled:opacity-70">
                   {addingBook ? 'Adding...' : 'Add Book'}
                 </button>
               </form>
            </div>
         </div>

         <div className="lg:col-span-2">
           <div className="bg-white rounded-3xl shadow-sm border border-slate-200 p-6 overflow-hidden">
             <h3 className="text-xl font-extrabold text-slate-900 mb-6 flex items-center gap-2">
               <BookOpen size={24} className="text-indigo-600" /> Catalog Management
             </h3>
             <div className="overflow-x-auto">
               <table className="w-full text-left border-collapse">
                 <thead>
                   <tr className="border-b-2 border-slate-100 uppercase text-xs font-bold text-slate-500 tracking-wider">
                     <th className="py-3 px-4">Book</th>
                     <th className="py-3 px-4 text-center">Price</th>
                     <th className="py-3 px-4 text-center">Actions</th>
                   </tr>
                 </thead>
                 <tbody>
                   {books.map(book => (
                     <tr key={book.id} className="border-b border-slate-50 hover:bg-slate-50 transition">
                       <td className="py-3 px-4">
                         <div className="font-bold text-slate-900">{book.title}</div>
                         <div className="text-sm text-slate-500">{book.author}</div>
                       </td>
                       <td className="py-3 px-4 text-center font-bold text-slate-700">
                         ${Number(book.price).toFixed(2)}
                       </td>
                       <td className="py-3 px-4 text-center">
                         <button 
                           onClick={() => handleDeleteBook(book.id)}
                           className="text-slate-400 hover:text-rose-500 p-2 rounded-lg hover:bg-rose-50 transition"
                           title="Delete Book"
                         >
                           <Trash2 size={18} />
                         </button>
                       </td>
                     </tr>
                   ))}
                 </tbody>
               </table>
               {books.length === 0 && (
                 <div className="text-center py-10 text-slate-500">No books in catalog. Add your first one!</div>
               )}
             </div>
           </div>
         </div>
      </div>
    </div>
  );
}
