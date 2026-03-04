import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api";
import { useCart } from "../context/CartContext";
import {
  ArrowLeft,
  ShoppingCart,
  Star,
  Calendar,
  BookOpen,
  AlertCircle,
} from "lucide-react";

export default function BookDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToCart } = useCart();
  const [book, setBook] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [addingToCart, setAddingToCart] = useState(false);

  useEffect(() => {
    const fetchBook = async () => {
      try {
        const res = await api.get(`/books/${id}`);
        setBook(res.data);
      } catch (err) {
        console.error("Book not found", err);
      } finally {
        setLoading(false);
      }
    };
    fetchBook();
  }, [id]);

  const handleAddToCart = async () => {
    setAddingToCart(true);
    await addToCart(Number(id), 1);
    setAddingToCart(false);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!book) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <AlertCircle size={48} className="mx-auto text-rose-500 mb-4" />
        <h2 className="text-2xl font-bold text-slate-900 mb-2">
          Book Not Found
        </h2>
        <p className="text-slate-500 mb-6">
          We couldn't find the book you were looking for.
        </p>
        <button
          onClick={() => navigate("/")}
          className="text-indigo-600 font-medium hover:underline"
        >
          Return to Catalog
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-slate-500 hover:text-indigo-600 transition mb-8 font-medium bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm inline-flex hover:shadow-md"
      >
        <ArrowLeft size={16} /> Back
      </button>

      <div className="bg-white rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100 p-8 sm:p-12">
        <div className="flex flex-col lg:flex-row gap-12">
          {/* Cover Image */}
          <div className="lg:w-1/3 flex-shrink-0">
            <div className="bg-slate-200 rounded-2xl w-full aspect-[2/3] relative overflow-hidden shadow-lg border border-slate-100">
              {book.cover_image_url ? (
                <img
                  src={book.cover_image_url}
                  alt={book.title}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-slate-400 font-medium text-lg">
                  No Cover Available
                </div>
              )}
            </div>
          </div>

          {/* Book Info */}
          <div className="lg:w-2/3 flex flex-col">
            <div className="inline-block px-3 py-1 bg-indigo-50 text-indigo-700 font-bold text-xs uppercase tracking-wider rounded-lg mb-4 w-max border border-indigo-100">
              {book.genre || "General"}
            </div>
            <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 mb-2 tracking-tight">
              {book.title}
            </h1>
            <p className="text-xl text-slate-500 font-medium mb-6">
              by {book.author}
            </p>

            <div className="flex items-center gap-6 mb-8 border-b border-slate-100 pb-8">
              <div className="flex items-center gap-2 bg-amber-50 px-3 py-1.5 rounded-xl border border-amber-100">
                <Star className="text-amber-500 fill-amber-500" size={20} />
                <span className="font-bold text-slate-800 text-lg">
                  {book.average_rating}
                </span>
              </div>
              <div className="flex flex-col">
                <span className="font-bold text-3xl text-slate-900">
                  ${Number(book.price).toFixed(2)}
                </span>
              </div>

              <button
                onClick={handleAddToCart}
                disabled={addingToCart}
                className="ml-auto bg-indigo-600 text-white font-bold py-3.5 px-8 rounded-xl hover:bg-indigo-700 hover:shadow-lg hover:shadow-indigo-600/20 active:scale-95 transition-all flex items-center gap-2 disabled:opacity-70 disabled:hover:scale-100"
              >
                {addingToCart ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mx-5"></div>
                ) : (
                  <>
                    <ShoppingCart size={20} /> Add to Cart
                  </>
                )}
              </button>
            </div>

            <div className="mb-8">
              <h3 className="text-lg font-bold text-slate-900 mb-3">
                Description
              </h3>
              <p className="text-slate-600 leading-relaxed max-w-3xl">
                {book.description || "No description provided for this book."}
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-slate-50 p-6 rounded-2xl border border-slate-100 mt-auto">
              <div className="flex items-center gap-3">
                <div className="bg-white p-2 rounded-lg text-slate-400 shadow-sm border border-slate-100">
                  <Calendar size={20} />
                </div>
                <div>
                  <div className="text-xs text-slate-400 font-bold uppercase tracking-wider">
                    Published
                  </div>
                  <div className="font-medium text-slate-800">
                    {book.publication_date
                      ? new Date(book.publication_date).toLocaleDateString()
                      : "N/A"}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="bg-white p-2 rounded-lg text-slate-400 shadow-sm border border-slate-100">
                  <BookOpen size={20} />
                </div>
                <div>
                  <div className="text-xs text-slate-400 font-bold uppercase tracking-wider">
                    Publisher
                  </div>
                  <div className="font-medium text-slate-800">
                    {book.publisher || "N/A"}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
