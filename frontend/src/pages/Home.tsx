import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import { Search, Sparkles, Star, ShoppingCart } from 'lucide-react';
import ReadingHistory from '../components/ReadingHistory';

export default function Home() {
  const { user } = useAuth();
  const { addToCart } = useCart();
  const [books, setBooks] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [searchMode, setSearchMode] = useState<'regular' | 'semantic'>('semantic');
  const [searching, setSearching] = useState(false);

  // Genre-based search result state
  const [matchedBook, setMatchedBook] = useState<any>(null);
  const [similarBooks, setSimilarBooks] = useState<any[]>([]);

  useEffect(() => {
    fetchInitialData();
  }, [user]);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      const [booksRes, recsRes] = await Promise.all([
        api.get('/books/'),
        user ? api.get('/ai/recommendations').catch(() => ({ data: [] })) : Promise.resolve({ data: [] })
      ]);
      setBooks(booksRes.data);
      setRecommendations(recsRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const clearSearch = () => {
    setMatchedBook(null);
    setSimilarBooks([]);
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) {
      clearSearch();
      fetchInitialData();
      return;
    }
    setSearching(true);
    try {
      if (searchMode === 'semantic') {
        clearSearch();
        const res = await api.get(`/ai/search`, { params: { query, limit: 12 } });
        setBooks(res.data);
      } else {
        // Try genre-based recommendation search first
        try {
          const res = await api.get('/books/search-with-recommendations', { params: { query } });
          setMatchedBook(res.data.matched_book);
          setSimilarBooks(res.data.similar_books);
          setBooks([]);
        } catch {
          // Fallback to regular search if no exact title match
          clearSearch();
          const res = await api.get(`/books/`, { params: { search: query } });
          setBooks(res.data);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  const BookCard = ({ book }: { book: any }) => (
    <div className="bg-white rounded-2xl shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border border-slate-100 flex flex-col overflow-hidden group">
      <div className="h-64 bg-slate-200 w-full relative overflow-hidden">
        {book.cover_image_url ? (
          <img src={book.cover_image_url} alt={book.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-slate-400 font-medium">No Cover</div>
        )}
        <div className="absolute top-3 right-3 bg-white/90 backdrop-blur border border-white/20 px-2.5 py-1 rounded-full text-xs font-bold text-slate-800 flex items-center gap-1 shadow-sm">
          <Star size={12} className="text-amber-500 fill-amber-500" /> {book.average_rating}
        </div>
      </div>
      <div className="p-5 flex flex-col flex-grow">
        <div className="text-xs font-bold uppercase tracking-wider text-indigo-600 mb-1">{book.genre}</div>
        <Link to={`/book/${book.id}`} className="font-bold text-lg text-slate-900 line-clamp-2 hover:text-indigo-600 transition mb-1">
          {book.title}
        </Link>
        <div className="text-slate-500 text-sm mb-4">{book.author}</div>
        <div className="mt-auto flex items-center justify-between">
          <span className="font-extrabold text-xl text-slate-900">${Number(book.price).toFixed(2)}</span>
          <button 
            onClick={() => addToCart(book.id, 1)}
            className="bg-slate-100 hover:bg-indigo-600 hover:text-white text-slate-700 p-2.5 rounded-xl transition-all shadow-sm active:scale-95"
            title="Add to Cart"
          >
            <ShoppingCart size={20} />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero / Search Section */}
      <div className="bg-indigo-900 rounded-3xl p-8 sm:p-12 mb-12 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden opacity-20 pointer-events-none">
          <div className="absolute -top-24 -right-24 w-96 h-96 bg-indigo-500 rounded-full blur-3xl mix-blend-screen"></div>
          <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-purple-500 rounded-full blur-3xl mix-blend-screen"></div>
        </div>
        
        <div className="relative z-10 max-w-3xl mx-auto text-center">
          <h1 className="text-4xl sm:text-5xl font-extrabold text-white mb-6 tracking-tight">
            Discover Your Next <span className="text-indigo-300">Great Read</span>
          </h1>
          <p className="text-indigo-100 text-lg mb-8 max-w-2xl mx-auto">
            Use our AI-powered semantic search to find books based on concepts, themes, or feelings rather than just exact keywords.
          </p>
          
          <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-grow group">
              <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none text-slate-400 group-focus-within:text-indigo-500 transition">
                {searchMode === 'semantic' ? <Sparkles size={20} /> : <Search size={20} />}
              </div>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={searchMode === 'semantic' ? "Try 'books about learning python from scratch'" : "Search by title, author..."}
                className="w-full pl-12 pr-4 py-4 rounded-xl shadow-lg border-0 ring-4 ring-white/10 focus:ring-white/30 text-slate-900 placeholder:text-slate-400 outline-none transition-all text-lg"
              />
            </div>
            <button
              type="submit"
              disabled={searching}
              className="px-8 py-4 bg-white text-indigo-900 font-bold rounded-xl shadow-lg hover:bg-indigo-50 hover:scale-105 active:scale-95 transition-all text-lg disabled:opacity-80 disabled:hover:scale-100"
            >
              {searching ? 'Finding...' : 'Search'}
            </button>
          </form>
          
          <div className="mt-4 flex items-center justify-center gap-4 text-sm font-medium text-indigo-200">
             <span>Mode:</span>
             <label className="flex items-center gap-1.5 cursor-pointer hover:text-white transition">
                <input type="radio" checked={searchMode === 'semantic'} onChange={() => setSearchMode('semantic')} className="accent-indigo-400" />
                AI Semantic
             </label>
             <label className="flex items-center gap-1.5 cursor-pointer hover:text-white transition">
                <input type="radio" checked={searchMode === 'regular'} onChange={() => setSearchMode('regular')} className="accent-indigo-400" />
                Keyword
             </label>
          </div>
        </div>
      </div>

      {/* Reading History Section */}
      {!query && <ReadingHistory />}

      {/* Recommendations Section */}
      {!query && recommendations.length > 0 && (
        <div className="mb-16">
          <div className="flex items-center gap-2 mb-6">
            <Sparkles className="text-amber-500" size={28} />
            <h2 className="text-2xl font-extrabold text-slate-900">{user ? "Recommended For You" : "Trending & Highly Rated"}</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
            {recommendations.slice(0, 6).map(book => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>
        </div>
      )}

      {/* Genre-Based Search Results */}
      {matchedBook && (
        <div className="mb-16">
          {/* Primary matched book */}
          <h2 className="text-2xl font-extrabold text-slate-900 mb-6 flex items-center gap-2">
            <Search size={24} className="text-indigo-500" /> Search Result
          </h2>
          <div className="bg-white rounded-3xl shadow-sm border border-slate-200 p-6 mb-10 flex flex-col sm:flex-row gap-6">
            <div className="w-full sm:w-48 h-64 rounded-2xl overflow-hidden bg-slate-200 flex-shrink-0">
              {matchedBook.cover_image_url ? (
                <img src={matchedBook.cover_image_url} alt={matchedBook.title} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-slate-400">No Cover</div>
              )}
            </div>
            <div className="flex flex-col flex-grow">
              <div className="text-xs font-bold uppercase tracking-wider text-indigo-600 mb-1">{matchedBook.genre}</div>
              <Link to={`/book/${matchedBook.id}`} className="text-2xl font-extrabold text-slate-900 hover:text-indigo-600 transition mb-2">
                {matchedBook.title}
              </Link>
              <div className="text-slate-500 mb-2">{matchedBook.author}</div>
              <div className="flex items-center gap-1 mb-3">
                <Star size={16} className="text-amber-500 fill-amber-500" />
                <span className="font-bold text-slate-700">{matchedBook.average_rating}</span>
              </div>
              {matchedBook.description && (
                <p className="text-slate-600 text-sm line-clamp-3 mb-4">{matchedBook.description}</p>
              )}
              <div className="mt-auto flex items-center gap-4">
                <span className="font-extrabold text-2xl text-slate-900">${Number(matchedBook.price).toFixed(2)}</span>
                <button
                  onClick={() => addToCart(matchedBook.id, 1)}
                  className="bg-indigo-600 text-white font-bold py-2.5 px-6 rounded-xl hover:bg-indigo-700 transition active:scale-95"
                >
                  Add to Cart
                </button>
              </div>
            </div>
          </div>

          {/* Similar books by genre */}
          {similarBooks.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-6">
                <Sparkles className="text-amber-500" size={24} />
                <h3 className="text-xl font-extrabold text-slate-900">
                  Similar Books in {matchedBook.genre}
                </h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
                {similarBooks.map((book: any) => (
                  <BookCard key={book.id} book={book} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Catalog / Generic Search Results */}
      <div>
        <h2 className="text-2xl font-extrabold text-slate-900 mb-6 flex items-center gap-2">
          {query && !matchedBook ? (
             <>{searchMode === 'semantic' ? <Sparkles size={24} className="text-indigo-500" /> : <Search size={24} className="text-indigo-500" />} Search Results</>
          ) : !matchedBook ? (
             "All Books"
          ) : null}
        </h2>
        
        {!matchedBook && (
          loading ? (
            <div className="flex justify-center py-20">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
          ) : books.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {books.map(book => (
                <BookCard key={book.id} book={book} />
              ))}
            </div>
          ) : query ? (
            <div className="text-center py-20 bg-white rounded-3xl border border-dashed border-slate-300">
              <p className="text-slate-500 text-lg">No books found matching your criteria.</p>
            </div>
          ) : (
            <div className="text-center py-20 bg-white rounded-3xl border border-dashed border-slate-300">
              <p className="text-slate-500 text-lg">No books in catalog yet.</p>
            </div>
          )
        )}
      </div>
    </div>
  );
}
