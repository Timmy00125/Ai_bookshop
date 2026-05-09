import React, { useState, useEffect } from 'react';
import api from '../api';
import {
  Shield, BookOpen, Plus, Trash2, RefreshCw, ShoppingBag, Package,
  CheckCircle, Users, Pencil, X, BarChart3, TrendingUp, UserCheck,
  Filter,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Navigate } from 'react-router-dom';

interface Analytics {
  total_users: number;
  total_books: number;
  total_orders: number;
  total_revenue: number;
  orders_by_status: Record<string, number>;
  users_by_role: Record<string, number>;
  recent_signups: number;
}

interface UserRecord {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

const KNOWN_GENRES = [
  "Fiction", "Non-Fiction", "Mystery", "Thriller", "Romance", "Science Fiction",
  "Fantasy", "Horror", "Biography", "History", "Self-Help", "Business",
  "Technology", "Science", "Philosophy", "Psychology", "Poetry", "Drama",
  "Travel", "Cooking", "Health", "Art", "Music", "Sports", "Education",
  "Children", "Young Adult", "Crime", "Adventure", "Western",
];

export default function AdminDashboard() {
  const { user } = useAuth();
  const [books, setBooks] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [users, setUsers] = useState<UserRecord[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [addingBook, setAddingBook] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [activeTab, setActiveTab] = useState<'books' | 'orders' | 'users'>('books');
  const [genres, setGenres] = useState<string[]>([]);
  const [selectedGenre, setSelectedGenre] = useState<string>('');

  // New/edit book state
  const [editingBook, setEditingBook] = useState<any>(null);
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [price, setPrice] = useState('');
  const [genre, setGenre] = useState('');
  const [customGenre, setCustomGenre] = useState('');
  const [useCustomGenre, setUseCustomGenre] = useState(false);
  const [description, setDescription] = useState('');
  const [coverUrl, setCoverUrl] = useState('');
  const [isbn, setIsbn] = useState('');
  const [publisher, setPublisher] = useState('');
  const [stockCount, setStockCount] = useState('');
  const [publicationDate, setPublicationDate] = useState('');

  useEffect(() => {
    fetchData();
    fetchGenres();
  }, []);

  const fetchGenres = async () => {
    try {
      const res = await api.get('/books/genres');
      setGenres(res.data.genres);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const [booksRes, ordersRes, usersRes, analyticsRes] = await Promise.all([
        api.get('/books/'),
        api.get('/orders/all'),
        api.get('/admin/users'),
        api.get('/admin/analytics'),
      ]);
      setBooks(booksRes.data);
      setOrders(ordersRes.data);
      setUsers(usersRes.data);
      setAnalytics(analyticsRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setTitle(''); setAuthor(''); setPrice(''); setGenre('');
    setDescription(''); setCoverUrl(''); setIsbn(''); setPublisher('');
    setStockCount(''); setPublicationDate(''); setEditingBook(null);
    setCustomGenre(''); setUseCustomGenre(false);
  };

  const startEdit = (book: any) => {
    setEditingBook(book);
    setTitle(book.title || '');
    setAuthor(book.author || '');
    setPrice(String(book.price || ''));
    setGenre(book.genre || '');
    setDescription(book.description || '');
    setCoverUrl(book.cover_image_url || '');
    setIsbn(book.isbn || '');
    setPublisher(book.publisher || '');
    setStockCount(String(book.stock_count || 0));
    setPublicationDate(book.publication_date ? new Date(book.publication_date).toISOString().split('T')[0] : '');
  };

  const handleAddOrEditBook = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddingBook(true);
    try {
      const finalGenre = useCustomGenre ? customGenre : genre;
      const payload: any = {
        title, author, price: parseFloat(price), genre: finalGenre, description,
        cover_image_url: coverUrl, isbn: isbn || undefined,
        publisher: publisher || undefined, stock_count: parseInt(stockCount) || 0,
      };
      if (publicationDate) {
        payload.publication_date = new Date(publicationDate).toISOString();
      }

      if (editingBook) {
        await api.put(`/books/${editingBook.id}`, payload);
      } else {
        await api.post('/books/', payload);
      }
      resetForm();
      await fetchData();
      await fetchGenres();
    } catch (err) {
      console.error(err);
      alert(editingBook ? 'Failed to update book' : 'Failed to add book');
    } finally {
      setAddingBook(false);
    }
  };

  const handleDeleteBook = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this book?")) return;
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

  const handleUpdateOrderStatus = async (orderId: number, newStatus: string) => {
    try {
      await api.patch(`/orders/${orderId}/status`, { status: newStatus });
      await fetchData();
    } catch (err) {
      console.error(err);
      alert('Failed to update order status');
    }
  };

  const handleToggleUserActive = async (userId: number, currentActive: boolean) => {
    try {
      await api.patch(`/admin/users/${userId}`, { is_active: !currentActive });
      await fetchData();
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.detail || 'Failed to update user');
    }
  };

  const handleChangeUserRole = async (userId: number, newRole: string) => {
    try {
      await api.patch(`/admin/users/${userId}`, { role: newRole });
      await fetchData();
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.detail || 'Failed to update user role');
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!window.confirm("Are you sure you want to delete this user? This action cannot be undone.")) return;
    try {
      await api.delete(`/admin/users/${userId}`);
      await fetchData();
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.detail || 'Failed to delete user');
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

  const totalRevenue = analytics?.total_revenue ?? orders.reduce((acc, order) => acc + parseFloat(order.total_price), 0);

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

      {/* Analytics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-12">
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <div className="flex items-center gap-2 mb-1">
            <BookOpen size={14} className="text-indigo-500" />
            <h3 className="text-slate-500 font-bold uppercase tracking-wider text-[10px]">Books</h3>
          </div>
          <div className="text-3xl font-extrabold text-slate-900">{analytics?.total_books ?? books.length}</div>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <div className="flex items-center gap-2 mb-1">
            <Users size={14} className="text-violet-500" />
            <h3 className="text-slate-500 font-bold uppercase tracking-wider text-[10px]">Users</h3>
          </div>
          <div className="text-3xl font-extrabold text-slate-900">{analytics?.total_users ?? users.length}</div>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <div className="flex items-center gap-2 mb-1">
            <ShoppingBag size={14} className="text-amber-500" />
            <h3 className="text-slate-500 font-bold uppercase tracking-wider text-[10px]">Orders</h3>
          </div>
          <div className="text-3xl font-extrabold text-slate-900">{analytics?.total_orders ?? orders.length}</div>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp size={14} className="text-emerald-500" />
            <h3 className="text-slate-500 font-bold uppercase tracking-wider text-[10px]">Revenue</h3>
          </div>
          <div className="text-3xl font-extrabold text-emerald-600">${totalRevenue.toFixed(2)}</div>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <div className="flex items-center gap-2 mb-1">
            <UserCheck size={14} className="text-cyan-500" />
            <h3 className="text-slate-500 font-bold uppercase tracking-wider text-[10px]">New (7d)</h3>
          </div>
          <div className="text-3xl font-extrabold text-slate-900">{analytics?.recent_signups ?? 0}</div>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <div className="flex items-center gap-2 mb-1">
            <BarChart3 size={14} className="text-rose-500" />
            <h3 className="text-slate-500 font-bold uppercase tracking-wider text-[10px]">Admins</h3>
          </div>
          <div className="text-3xl font-extrabold text-slate-900">{analytics?.users_by_role?.admin ?? 0}</div>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle size={14} className="text-emerald-500" />
            <h3 className="text-slate-500 font-bold uppercase tracking-wider text-[10px]">Completed</h3>
          </div>
          <div className="text-3xl font-extrabold text-slate-900">{analytics?.orders_by_status?.completed ?? 0}</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 mb-8 border-b border-slate-200">
        {[
          { key: 'books' as const, icon: <BookOpen size={16} />, label: 'Books' },
          { key: 'orders' as const, icon: <ShoppingBag size={16} />, label: 'Orders' },
          { key: 'users' as const, icon: <Users size={16} />, label: 'Users' },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`pb-3 text-sm font-bold uppercase tracking-wider transition ${activeTab === tab.key ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-slate-500 hover:text-slate-700'}`}
          >
            <span className="flex items-center gap-2">{tab.icon} {tab.label}</span>
          </button>
        ))}
      </div>

      {/* Books Tab */}
      {activeTab === 'books' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1">
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 sticky top-24">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
                  {editingBook ? <><Pencil size={24} className="text-indigo-600" /> Edit Book</> : <><Plus size={24} className="text-indigo-600" /> Add New Book</>}
                </h3>
                {editingBook && (
                  <button onClick={resetForm} className="text-slate-400 hover:text-slate-600 p-1">
                    <X size={20} />
                  </button>
                )}
              </div>
              <form onSubmit={handleAddOrEditBook} className="space-y-4">
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
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Stock</label>
                    <input type="number" value={stockCount} onChange={e => setStockCount(e.target.value)} className="w-full px-4 py-2 bg-slate-50 rounded-lg border border-slate-200 focus:bg-white focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition" />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Genre</label>
                  <div className="flex items-center gap-2 mb-2">
                    <label className="flex items-center gap-1 text-sm text-slate-600 cursor-pointer">
                      <input type="checkbox" checked={useCustomGenre} onChange={e => setUseCustomGenre(e.target.checked)} className="accent-indigo-600" />
                      Custom genre
                    </label>
                  </div>
                  {useCustomGenre ? (
                    <input required type="text" value={customGenre} onChange={e => setCustomGenre(e.target.value)} placeholder="Enter custom genre" className="w-full px-4 py-2 bg-slate-50 rounded-lg border border-slate-200 focus:bg-white focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition" />
                  ) : (
                    <select required value={genre} onChange={e => setGenre(e.target.value)} className="w-full px-4 py-2 bg-slate-50 rounded-lg border border-slate-200 focus:bg-white focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition">
                      <option value="">Select genre</option>
                      {KNOWN_GENRES.map(g => (
                        <option key={g} value={g}>{g}</option>
                      ))}
                    </select>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">ISBN</label>
                    <input type="text" value={isbn} onChange={e => setIsbn(e.target.value)} className="w-full px-4 py-2 bg-slate-50 rounded-lg border border-slate-200 focus:bg-white focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition" />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Pub. Date</label>
                    <input type="date" value={publicationDate} onChange={e => setPublicationDate(e.target.value)} className="w-full px-4 py-2 bg-slate-50 rounded-lg border border-slate-200 focus:bg-white focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition" />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Publisher</label>
                  <input type="text" value={publisher} onChange={e => setPublisher(e.target.value)} className="w-full px-4 py-2 bg-slate-50 rounded-lg border border-slate-200 focus:bg-white focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Cover Image URL</label>
                  <input type="text" value={coverUrl} onChange={e => setCoverUrl(e.target.value)} className="w-full px-4 py-2 bg-slate-50 rounded-lg border border-slate-200 focus:bg-white focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Description</label>
                  <textarea rows={3} value={description} onChange={e => setDescription(e.target.value)} className="w-full px-4 py-2 bg-slate-50 rounded-lg border border-slate-200 focus:bg-white focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition"></textarea>
                </div>
                <div className="flex gap-3">
                  <button type="submit" disabled={addingBook} className="flex-1 bg-indigo-600 text-white font-bold py-3 rounded-xl hover:bg-indigo-700 transition disabled:opacity-70">
                    {addingBook ? 'Saving...' : editingBook ? 'Update Book' : 'Add Book'}
                  </button>
                  {editingBook && (
                    <button type="button" onClick={resetForm} className="px-4 py-3 bg-slate-100 text-slate-700 font-bold rounded-xl hover:bg-slate-200 transition">
                      Cancel
                    </button>
                  )}
                </div>
              </form>
            </div>
          </div>

          <div className="lg:col-span-2">
            <div className="bg-white rounded-3xl shadow-sm border border-slate-200 p-6 overflow-hidden">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
                  <BookOpen size={24} className="text-indigo-600" /> Catalog Management
                </h3>
                <div className="flex items-center gap-2">
                  <Filter size={16} className="text-slate-400" />
                  <select
                    value={selectedGenre}
                    onChange={e => setSelectedGenre(e.target.value)}
                    className="text-sm bg-white border border-slate-200 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none"
                  >
                    <option value="">All Genres</option>
                    {genres.map(g => (
                      <option key={g} value={g}>{g}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b-2 border-slate-100 uppercase text-xs font-bold text-slate-500 tracking-wider">
                      <th className="py-3 px-4">Book</th>
                      <th className="py-3 px-4">Genre</th>
                      <th className="py-3 px-4 text-center">Price</th>
                      <th className="py-3 px-4 text-center">Stock</th>
                      <th className="py-3 px-4 text-center">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {books
                      .filter(book => !selectedGenre || book.genre === selectedGenre)
                      .map(book => (
                        <tr key={book.id} className="border-b border-slate-50 hover:bg-slate-50 transition">
                          <td className="py-3 px-4">
                            <div className="font-bold text-slate-900">{book.title}</div>
                            <div className="text-sm text-slate-500">{book.author}</div>
                          </td>
                          <td className="py-3 px-4">
                            <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-2 py-1 rounded-full">
                              {book.genre}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-center font-bold text-slate-700">
                            ${Number(book.price).toFixed(2)}
                          </td>
                          <td className="py-3 px-4 text-center text-slate-600">
                            {book.stock_count}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <div className="flex items-center justify-center gap-1">
                              <button
                                onClick={() => startEdit(book)}
                                className="text-slate-400 hover:text-indigo-500 p-2 rounded-lg hover:bg-indigo-50 transition"
                                title="Edit Book"
                              >
                                <Pencil size={16} />
                              </button>
                              <button
                                onClick={() => handleDeleteBook(book.id)}
                                className="text-slate-400 hover:text-rose-500 p-2 rounded-lg hover:bg-rose-50 transition"
                                title="Delete Book"
                              >
                                <Trash2 size={16} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
                {books.filter(book => !selectedGenre || book.genre === selectedGenre).length === 0 && (
                  <div className="text-center py-10 text-slate-500">
                    {selectedGenre ? `No books found in "${selectedGenre}" genre.` : 'No books in catalog. Add your first one!'}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Orders Tab */}
      {activeTab === 'orders' && (
        <div className="bg-white rounded-3xl shadow-sm border border-slate-200 p-6 overflow-hidden">
          <h3 className="text-xl font-extrabold text-slate-900 mb-6 flex items-center gap-2">
            <Package size={24} className="text-indigo-600" /> Order Management
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b-2 border-slate-100 uppercase text-xs font-bold text-slate-500 tracking-wider">
                  <th className="py-3 px-4">Order ID</th>
                  <th className="py-3 px-4">Customer</th>
                  <th className="py-3 px-4">Items</th>
                  <th className="py-3 px-4 text-center">Total</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-center">Date</th>
                  <th className="py-3 px-4 text-center">Update</th>
                </tr>
              </thead>
              <tbody>
                {orders.map(order => (
                  <tr key={order.id} className="border-b border-slate-50 hover:bg-slate-50 transition">
                    <td className="py-3 px-4 font-mono text-slate-700">#{order.id}</td>
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">{order.user?.username || 'User #' + order.user_id}</div>
                    </td>
                    <td className="py-3 px-4">
                      <ul className="text-sm text-slate-600">
                        {order.items?.map((item: any) => (
                          <li key={item.id}>{item.quantity}x {item.book?.title || 'Book #' + item.book_id}</li>
                        ))}
                      </ul>
                    </td>
                    <td className="py-3 px-4 text-center font-bold text-slate-700">
                      ${Number(order.total_price).toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${
                        order.status === 'completed'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : order.status === 'cancelled'
                          ? 'bg-rose-50 text-rose-700 border border-rose-200'
                          : 'bg-amber-50 text-amber-700 border border-amber-200'
                      }`}>
                        {order.status === 'completed' && <CheckCircle size={12} />}
                        {order.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center text-sm text-slate-500">
                      {new Date(order.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <select
                        value={order.status}
                        onChange={(e) => handleUpdateOrderStatus(order.id, e.target.value)}
                        className="text-sm bg-white border border-slate-200 rounded-lg px-2 py-1 focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none"
                      >
                        <option value="pending">Pending</option>
                        <option value="completed">Completed</option>
                        <option value="cancelled">Cancelled</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {orders.length === 0 && (
              <div className="text-center py-10 text-slate-500">No orders yet.</div>
            )}
          </div>
        </div>
      )}

      {/* Users Tab */}
      {activeTab === 'users' && (
        <div className="bg-white rounded-3xl shadow-sm border border-slate-200 p-6 overflow-hidden">
          <h3 className="text-xl font-extrabold text-slate-900 mb-6 flex items-center gap-2">
            <Users size={24} className="text-indigo-600" /> User Management
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b-2 border-slate-100 uppercase text-xs font-bold text-slate-500 tracking-wider">
                  <th className="py-3 px-4">ID</th>
                  <th className="py-3 px-4">User</th>
                  <th className="py-3 px-4">Email</th>
                  <th className="py-3 px-4 text-center">Role</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-center">Joined</th>
                  <th className="py-3 px-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id} className="border-b border-slate-50 hover:bg-slate-50 transition">
                    <td className="py-3 px-4 font-mono text-slate-500">#{u.id}</td>
                    <td className="py-3 px-4 font-bold text-slate-900">{u.username}</td>
                    <td className="py-3 px-4 text-slate-600">{u.email}</td>
                    <td className="py-3 px-4 text-center">
                      <select
                        value={u.role}
                        onChange={(e) => handleChangeUserRole(u.id, e.target.value)}
                        disabled={u.id === user?.id}
                        className="text-xs font-bold uppercase bg-white border border-slate-200 rounded-lg px-2 py-1 focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <option value="user">User</option>
                        <option value="admin">Admin</option>
                      </select>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${
                        u.is_active
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-rose-50 text-rose-700 border border-rose-200'
                      }`}>
                        {u.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center text-sm text-slate-500">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <button
                          onClick={() => handleToggleUserActive(u.id, u.is_active)}
                          disabled={u.id === user?.id}
                          className={`p-2 rounded-lg transition disabled:opacity-30 disabled:cursor-not-allowed ${
                            u.is_active
                              ? 'text-amber-500 hover:bg-amber-50'
                              : 'text-emerald-500 hover:bg-emerald-50'
                          }`}
                          title={u.is_active ? 'Deactivate' : 'Activate'}
                        >
                          {u.is_active ? <X size={16} /> : <CheckCircle size={16} />}
                        </button>
                        <button
                          onClick={() => handleDeleteUser(u.id)}
                          disabled={u.id === user?.id}
                          className="text-slate-400 hover:text-rose-500 p-2 rounded-lg hover:bg-rose-50 transition disabled:opacity-30 disabled:cursor-not-allowed"
                          title="Delete User"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {users.length === 0 && (
              <div className="text-center py-10 text-slate-500">No users found.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
