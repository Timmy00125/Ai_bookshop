import { useState, useEffect } from "react";
import api from "../api";
import { Package, Calendar, Tag } from "lucide-react";
import { Link } from "react-router-dom";

export default function Orders() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        const res = await api.get("/orders/");
        setOrders(res.data);
      } catch (err) {
        console.error("Failed to fetch orders", err);
      } finally {
        setLoading(false);
      }
    };
    fetchOrders();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <div className="w-24 h-24 bg-slate-100 text-slate-300 rounded-full flex items-center justify-center mx-auto mb-6">
          <Package size={48} />
        </div>
        <h2 className="text-2xl font-bold text-slate-900 mb-2 tracking-tight">
          No Order History
        </h2>
        <p className="text-slate-500 mb-8 max-w-sm mx-auto">
          You haven't placed any simulated orders yet.
        </p>
        <Link
          to="/"
          className="bg-indigo-600 text-white font-bold py-3 pt-3.5 px-8 rounded-xl hover:bg-indigo-700 transition inline-block shadow-sm"
        >
          Explore Catalog
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 lg:py-12">
      <h1 className="text-3xl font-extrabold text-slate-900 mb-8 tracking-tight flex items-center gap-3">
        <Package size={32} className="text-indigo-600" /> My Orders
      </h1>

      <div className="space-y-6">
        {orders.map((order) => (
          <div
            key={order.id}
            className="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden transform transition hover:shadow-md"
          >
            <div className="bg-slate-50 border-b border-slate-200 p-4 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex flex-wrap gap-6 text-sm">
                <div>
                  <span className="block text-slate-500 font-medium uppercase text-xs tracking-wider mb-1">
                    Order Placed
                  </span>
                  <span className="font-bold text-slate-900 flex items-center gap-2">
                    <Calendar size={16} className="text-slate-400" />
                    {new Date(order.created_at).toLocaleDateString(undefined, {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </span>
                </div>
                <div>
                  <span className="block text-slate-500 font-medium uppercase text-xs tracking-wider mb-1">
                    TotalAmount
                  </span>
                  <span className="font-bold text-indigo-600 text-base">
                    ${Number(order.total_price).toFixed(2)}
                  </span>
                </div>
                <div>
                  <span className="block text-slate-500 font-medium uppercase text-xs tracking-wider mb-1">
                    Order Number
                  </span>
                  <span className="font-mono text-slate-700 font-bold flex items-center gap-2">
                    <Tag size={16} className="text-slate-400" />
                    ORD-{order.id.toString().padStart(5, "0")}
                  </span>
                </div>
              </div>
              <div className="inline-flex items-center gap-2 bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold px-4 py-2 rounded-full uppercase text-xs tracking-wider w-max">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                {order.status}
              </div>
            </div>

            <div className="p-4 sm:p-6">
              <div className="space-y-6">
                {order.items?.map((item: any) => (
                  <div
                    key={item.id}
                    className="flex gap-4 sm:gap-6 items-center"
                  >
                    <div className="w-20 h-28 sm:w-24 sm:h-36 bg-slate-200 rounded-lg overflow-hidden flex-shrink-0 shadow-sm border border-slate-100">
                      {item.book.cover_image_url ? (
                        <img
                          src={item.book.cover_image_url}
                          alt={item.book.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-[10px] text-slate-400">
                          No Cover
                        </div>
                      )}
                    </div>
                    <div>
                      <h4 className="font-bold text-slate-900 sm:text-lg mb-1 line-clamp-2 hover:text-indigo-600 transition">
                        <Link to={`/book/${item.book_id}`}>
                          {item.book.title}
                        </Link>
                      </h4>
                      <p className="text-sm text-slate-500 mb-2">
                        {item.book.author}
                      </p>
                      <div className="flex items-center gap-4 text-sm font-medium text-slate-700">
                        <span>Qty: {item.quantity}</span>
                        <span className="font-bold">
                          ${Number(item.unit_price).toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
