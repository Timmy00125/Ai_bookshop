import { useState } from "react";
import { useCart } from "../context/CartContext";
import { useAuth } from "../context/AuthContext";
import { Link, useNavigate } from "react-router-dom";
import api from "../api";
import {
  Trash2,
  ShoppingBag,
  ShoppingCart,
  Plus,
  Minus,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";

export default function Cart() {
  const { cart, removeFromCart, updateQuantity, clearCart } = useCart();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [checkingOut, setCheckingOut] = useState(false);
  const [success, setSuccess] = useState(false);

  const total = cart.reduce(
    (acc, item) => acc + item.book.price * item.quantity,
    0,
  );

  const handleCheckout = async () => {
    if (!user) {
      navigate("/login");
      return;
    }
    setCheckingOut(true);
    try {
      await api.post("/orders/checkout");
      clearCart();
      setSuccess(true);
    } catch (err) {
      console.error("Checkout failed", err);
    } finally {
      setCheckingOut(false);
    }
  };

  if (success) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center">
        <div className="w-20 h-20 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-6">
          <ShieldCheck size={40} />
        </div>
        <h2 className="text-3xl font-extrabold text-slate-900 mb-4 tracking-tight">
          Order Confirmed!
        </h2>
        <p className="text-slate-500 text-lg mb-8 max-w-lg mx-auto">
          Thank you for your purchase. We've simulated the checkout process and
          your books will be delivered digitally (in theory!).
        </p>
        <div className="flex justify-center gap-4">
          <Link
            to="/orders"
            className="bg-indigo-600 text-white font-bold py-3 px-6 rounded-xl hover:bg-indigo-700 transition"
          >
            View Orders
          </Link>
          <Link
            to="/"
            className="bg-white text-indigo-600 font-bold py-3 px-6 rounded-xl border border-indigo-200 hover:bg-indigo-50 transition"
          >
            Continue Shopping
          </Link>
        </div>
      </div>
    );
  }

  if (cart.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <div className="w-24 h-24 bg-slate-100 text-slate-300 rounded-full flex items-center justify-center mx-auto mb-6">
          <ShoppingBag size={48} />
        </div>
        <h2 className="text-2xl font-bold text-slate-900 mb-2 tracking-tight">
          Your Cart is Empty
        </h2>
        <p className="text-slate-500 mb-8 max-w-sm mx-auto">
          Looks like you haven't added any books to your cart yet. Discover your
          next read!
        </p>
        <Link
          to="/"
          className="bg-indigo-600 text-white font-bold py-3 pt-3.5 px-8 rounded-xl hover:bg-indigo-700 hover:shadow-lg transition inline-block"
        >
          Explore Catalog
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-12">
      <h1 className="text-3xl font-extrabold text-slate-900 mb-8 tracking-tight flex items-center gap-3">
        <ShoppingCart size={32} className="text-indigo-600" /> Your Shopping
        Cart
      </h1>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Cart Items */}
        <div className="lg:w-2/3 space-y-4">
          {cart.map((item) => (
            <div
              key={item.id}
              className="bg-white p-4 sm:p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col sm:flex-row gap-6 items-center group transition-all hover:border-slate-200"
            >
              <div className="w-24 h-36 bg-slate-200 rounded-lg overflow-hidden flex-shrink-0 border border-slate-100 shadow-sm">
                {item.book.cover_image_url ? (
                  <img
                    src={item.book.cover_image_url}
                    alt={item.book.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-xs text-slate-400">
                    No Cover
                  </div>
                )}
              </div>

              <div className="flex-grow flex flex-col w-full text-center sm:text-left">
                <div className="text-xs font-bold text-indigo-600 uppercase tracking-wider mb-1">
                  {item.book.genre}
                </div>
                <Link
                  to={`/book/${item.book.id}`}
                  className="font-bold text-lg text-slate-900 hover:text-indigo-600 transition truncate mb-1"
                >
                  {item.book.title}
                </Link>
                <div className="text-slate-500 text-sm mb-4">
                  {item.book.author}
                </div>

                <div className="mt-auto flex items-center justify-between">
                  <span className="font-extrabold text-xl text-slate-900">
                    ${(item.book.price * item.quantity).toFixed(2)}
                  </span>

                  <div className="flex items-center gap-3">
                    <div className="flex items-center bg-slate-50 border border-slate-200 rounded-xl overflow-hidden">
                      <button
                        onClick={() =>
                          updateQuantity(
                            item.id,
                            Math.max(1, item.quantity - 1),
                          )
                        }
                        className="p-2 text-slate-500 hover:text-indigo-600 hover:bg-slate-100 transition"
                      >
                        <Minus size={16} />
                      </button>
                      <span className="w-10 text-center font-bold text-slate-700">
                        {item.quantity}
                      </span>
                      <button
                        onClick={() =>
                          updateQuantity(item.id, item.quantity + 1)
                        }
                        className="p-2 text-slate-500 hover:text-indigo-600 hover:bg-slate-100 transition"
                      >
                        <Plus size={16} />
                      </button>
                    </div>
                    <button
                      onClick={() => removeFromCart(item.id)}
                      className="p-2.5 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-xl transition"
                      title="Remove Item"
                    >
                      <Trash2 size={20} />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Order Summary */}
        <div className="lg:w-1/3">
          <div className="bg-white rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100 p-6 sm:p-8 sticky top-24">
            <h3 className="text-xl font-extrabold text-slate-900 mb-6 tracking-tight">
              Order Summary
            </h3>

            <div className="space-y-4 mb-6 text-sm">
              <div className="flex justify-between text-slate-500 font-medium">
                <span>Subtotal ({cart.length} items)</span>
                <span className="text-slate-900 font-semibold">
                  ${total.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between text-slate-500 font-medium">
                <span>Shipping</span>
                <span className="text-emerald-600 font-bold uppercase text-xs tracking-wider">
                  Free
                </span>
              </div>
              <div className="flex justify-between text-slate-500 font-medium">
                <span>Tax</span>
                <span className="text-slate-900 font-semibold">$0.00</span>
              </div>
            </div>

            <div className="border-t border-slate-100 pt-6 mb-8">
              <div className="flex justify-between items-end">
                <span className="text-slate-900 font-bold">Total</span>
                <span className="text-3xl font-extrabold text-indigo-600">
                  ${total.toFixed(2)}
                </span>
              </div>
            </div>

            <button
              onClick={handleCheckout}
              disabled={checkingOut}
              className="w-full bg-indigo-600 text-white font-bold py-4 rounded-xl hover:bg-indigo-700 hover:shadow-lg hover:shadow-indigo-600/20 active:scale-[0.98] transition-all flex justify-center items-center gap-2 disabled:opacity-70 disabled:hover:scale-100"
            >
              {checkingOut ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                <>
                  Simulate Checkout <ArrowRight size={20} />
                </>
              )}
            </button>
            <p className="text-center text-xs text-slate-400 mt-4">
              This is a prototype. No real payment will be processed.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
