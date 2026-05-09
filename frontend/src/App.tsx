import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';

import Layout from './components/Layout';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import BookDetail from './pages/BookDetail';
import Cart from './pages/Cart';
import Orders from './pages/Orders';
import AdminDashboard from './pages/AdminDashboard';

function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="book/:id" element={<BookDetail />} />
          <Route path="cart" element={<Cart />} />
          <Route path="orders" element={user ? <Orders /> : <Navigate to="/login" />} />
          <Route path="admin" element={user?.role === 'admin' ? <AdminDashboard /> : <Navigate to="/" />} />
          <Route path="login" element={user ? <Navigate to="/" /> : <Login />} />
          <Route path="register" element={user ? <Navigate to="/" /> : <Register />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
