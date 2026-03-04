import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import { BookOpen, ShoppingCart, User, LogOut, Shield } from 'lucide-react';
import Chatbot from './Chatbot';

export default function Layout() {
  const { user, logout } = useAuth();
  const { cart } = useCart();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const cartCount = cart.reduce((acc, item) => acc + item.quantity, 0);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans flex flex-col">
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200 shadow-sm transition-all duration-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <Link to="/" className="flex items-center gap-2 group">
              <div className="bg-indigo-600 text-white p-2 rounded-lg group-hover:bg-indigo-700 transition shadow-sm group-hover:shadow-md">
                <BookOpen size={24} />
              </div>
              <span className="font-bold text-xl tracking-tight text-indigo-950">AI Bookshop</span>
            </Link>
            
            <nav className="flex items-center gap-6">
              {user ? (
                <>
                  {user.role === 'admin' && (
                    <Link to="/admin" className="text-slate-600 hover:text-indigo-600 font-medium flex items-center gap-1 transition">
                      <Shield size={18} /> Admin
                    </Link>
                  )}
                  <Link to="/orders" className="text-slate-600 hover:text-indigo-600 font-medium transition">
                    Orders
                  </Link>
                  <Link to="/cart" className="relative text-slate-600 hover:text-indigo-600 transition group p-2 rounded-full hover:bg-slate-100">
                    <ShoppingCart size={24} />
                    {cartCount > 0 && (
                      <span className="absolute top-0 right-0 bg-rose-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full border-2 border-white pointer-events-none transform translate-x-1 -translate-y-1">
                        {cartCount}
                      </span>
                    )}
                  </Link>
                  <div className="flex items-center gap-3 ml-4 pl-4 border-l border-slate-200">
                    <span className="text-sm font-medium text-slate-700 flex items-center gap-1.5 bg-slate-100 px-3 py-1.5 rounded-full">
                      <User size={14} className="text-slate-500" />
                      {user.username}
                    </span>
                    <button onClick={handleLogout} className="text-slate-400 hover:text-rose-500 transition p-2 hover:bg-rose-50 rounded-full" title="Logout">
                      <LogOut size={20} />
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <Link to="/login" className="text-slate-600 hover:text-indigo-600 font-medium transition">Login</Link>
                  <Link to="/register" className="bg-indigo-600 text-white px-5 py-2.5 rounded-lg font-medium hover:bg-indigo-700 shadow-sm hover:shadow-md transition">Sign Up</Link>
                </>
              )}
            </nav>
          </div>
        </div>
      </header>

      <main className="flex-grow w-full relative">
        <Outlet />
      </main>

      <footer className="bg-slate-900 border-t border-slate-800 py-12 mt-12 text-slate-400 text-center">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-center items-center gap-2 mb-4">
             <BookOpen size={24} className="text-indigo-400 opacity-80" />
             <span className="font-bold text-xl text-white tracking-tight">AI Bookshop</span>
          </div>
          <p className="opacity-60 text-sm">© 2026 AI-Enhanced Online Bookshop Prototype.</p>
        </div>
      </footer>
      <Chatbot />
    </div>
  );
}
