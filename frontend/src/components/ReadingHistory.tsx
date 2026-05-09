import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, Star } from 'lucide-react';
import api from '../api';
import { useAuth } from '../context/AuthContext';

interface Book {
  id: number;
  title: string;
  author: string;
  genre: string;
  cover_image_url: string;
  average_rating: number;
  price: number;
}

export default function ReadingHistory() {
  const { user } = useAuth();
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    const fetchHistory = async () => {
      try {
        const res = await api.get('/users/reading-history', { params: { limit: 10 } });
        setBooks(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, [user]);

  if (!user || loading || books.length === 0) return null;

  return (
    <div className="mb-16">
      <div className="flex items-center gap-2 mb-6">
        <BookOpen className="text-emerald-500" size={28} />
        <h2 className="text-2xl font-extrabold text-slate-900">Books you've read before</h2>
      </div>
      <div className="flex gap-4 overflow-x-auto pb-4 -mx-4 px-4 scrollbar-thin">
        {books.map((book) => (
          <Link
            key={book.id}
            to={`/book/${book.id}`}
            className="flex-shrink-0 w-44 group"
          >
            <div className="h-56 rounded-2xl overflow-hidden bg-slate-200 shadow-sm group-hover:shadow-xl group-hover:-translate-y-1 transition-all duration-300 relative">
              {book.cover_image_url ? (
                <img
                  src={book.cover_image_url}
                  alt={book.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-slate-400 font-medium">
                  No Cover
                </div>
              )}
              <div className="absolute top-2 right-2 bg-white/90 backdrop-blur px-2 py-0.5 rounded-full text-xs font-bold text-slate-800 flex items-center gap-1 shadow-sm">
                <Star size={10} className="text-amber-500 fill-amber-500" /> {book.average_rating}
              </div>
            </div>
            <div className="mt-2 px-1">
              <div className="font-bold text-sm text-slate-900 line-clamp-2 group-hover:text-indigo-600 transition">
                {book.title}
              </div>
              <div className="text-xs text-slate-500 mt-0.5">{book.author}</div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
