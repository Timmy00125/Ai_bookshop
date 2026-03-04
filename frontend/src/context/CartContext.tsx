import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api';
import { useAuth } from './AuthContext';

interface CartItem {
  id: number;
  book_id: number;
  quantity: number;
  book: any;
}

interface CartContextType {
  cart: CartItem[];
  addToCart: (bookId: number, quantity: number) => Promise<void>;
  removeFromCart: (itemId: number) => Promise<void>;
  updateQuantity: (itemId: number, quantity: number) => Promise<void>;
  clearCart: () => void;
  refreshCart: () => Promise<void>;
  loading: boolean;
}

const CartContext = createContext<CartContextType>({} as CartContextType);

export const CartProvider: React.FC<{children: React.ReactNode}> = ({ children }) => {
  const [cart, setCart] = useState<CartItem[]>([]);
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();

  const refreshCart = async () => {
    if (!user) {
      setCart([]);
      return;
    }
    setLoading(true);
    try {
      const res = await api.get('/cart/');
      setCart(res.data);
    } catch (err) {
      console.error("Failed to fetch cart", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshCart();
  }, [user]);

  const addToCart = async (bookId: number, quantity: number = 1) => {
    if (!user) return; // Unauthenticated flow could use localstorage but PRD simulates cart internally for auth users.
    await api.post('/cart/', { book_id: bookId, quantity });
    await refreshCart();
  };

  const removeFromCart = async (itemId: number) => {
    if (!user) return;
    await api.delete(`/cart/${itemId}`);
    await refreshCart();
  };

  const updateQuantity = async (itemId: number, quantity: number) => {
    if (!user) return;
    await api.put(`/cart/${itemId}`, { quantity });
    await refreshCart();
  };

  const clearCart = () => {
    setCart([]);
  };

  return (
    <CartContext.Provider value={{ cart, addToCart, removeFromCart, updateQuantity, clearCart, refreshCart, loading }}>
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => useContext(CartContext);
