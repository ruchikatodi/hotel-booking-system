"""
Recommendations Routes
Handles retrieval and filtering of travel recommendations
Places to visit, cafes, restaurants, tourist spots near the hotel
"""

from flask import Blueprint, request, jsonify
from app import db
from app.models import Recommendation
from app.utils.exceptions import ValidationException
import traceback

bp = Blueprint('recommendations', __name__)


# ============================================
# GET ALL RECOMMENDATIONS (WITH FILTERS)
# ============================================

@bp.route('', methods=['GET'])
def get_recommendations():
    """
    Get all recommendations with optional filters
    
    Query Parameters (optional):
    - category: cafe, restaurant, tourist_spot, shopping, nightlife, cultural
    - price_range: budget, moderate, expensive
    - min_rating: minimum rating (1-5)
    - sort: rating_desc, rating_asc, price_asc, price_desc
    - limit: number of results (default: 50)
    
    Examples:
    GET /api/recommendations
    GET /api/recommendations?category=cafe
    GET /api/recommendations?category=restaurant&price_range=budget
    GET /api/recommendations?min_rating=4.5&sort=rating_desc
    
    Response:
    {
        "total": 13,
        "recommendations": [
            {
                "recommendation_id": 1,
                "title": "Brew Haven Coffee Shop",
                "category": "cafe",
                "description": "Cozy coffee shop...",
                "address": "123 Main Street",
                "rating": 4.5,
                "price_range": "budget"
            },
            ...
        ]
    }
    """
    try:
        print("🔍 Getting recommendations...")
        
        # Base query - only active recommendations
        query = Recommendation.query.filter_by(is_active=True)
        
        # Filter by category
        category = request.args.get('category')
        if category:
            valid_categories = ['cafe', 'restaurant', 'tourist_spot', 'shopping', 'nightlife', 'cultural']
            if category not in valid_categories:
                raise ValidationException(
                    f"Invalid category. Valid options: {', '.join(valid_categories)}",
                    field='category'
                )
            query = query.filter_by(category=category)
            print(f"✅ Filtered by category: {category}")
        
        # Filter by price range
        price_range = request.args.get('price_range')
        if price_range:
            valid_ranges = ['budget', 'moderate', 'expensive']
            if price_range not in valid_ranges:
                raise ValidationException(
                    f"Invalid price_range. Valid options: {', '.join(valid_ranges)}",
                    field='price_range'
                )
            query = query.filter_by(price_range=price_range)
            print(f"✅ Filtered by price: {price_range}")
        
        # Filter by minimum rating
        min_rating = request.args.get('min_rating', type=float)
        if min_rating:
            if not 1 <= min_rating <= 5:
                raise ValidationException(
                    "Rating must be between 1 and 5",
                    field='min_rating'
                )
            query = query.filter(Recommendation.rating >= min_rating)
            print(f"✅ Filtered by min rating: {min_rating}")
        
        # Sort results
        sort = request.args.get('sort', 'rating_desc')
        if sort == 'rating_desc':
            query = query.order_by(Recommendation.rating.desc())
        elif sort == 'rating_asc':
            query = query.order_by(Recommendation.rating.asc())
        elif sort == 'price_asc':
            # Order by price: budget -> moderate -> expensive
            query = query.order_by(
                db.case(
                    (Recommendation.price_range == 'budget', 1),
                    (Recommendation.price_range == 'moderate', 2),
                    (Recommendation.price_range == 'expensive', 3)
                )
            )
        elif sort == 'price_desc':
            # Order by price: expensive -> moderate -> budget
            query = query.order_by(
                db.case(
                    (Recommendation.price_range == 'expensive', 1),
                    (Recommendation.price_range == 'moderate', 2),
                    (Recommendation.price_range == 'budget', 3)
                )
            )
        
        # Apply limit
        limit = request.args.get('limit', 50, type=int)
        if limit < 1 or limit > 100:
            limit = 50
        query = query.limit(limit)
        
        # Execute query
        recommendations = query.all()
        
        print(f"✅ Found {len(recommendations)} recommendations")
        
        return jsonify({
            'total': len(recommendations),
            'filters_applied': {
                'category': category,
                'price_range': price_range,
                'min_rating': min_rating,
                'sort': sort
            },
            'recommendations': [rec.to_dict() for rec in recommendations]
        }), 200
        
    except ValidationException as e:
        print(f"❌ Validation error: {e.message}")
        return jsonify(e.to_dict()), 400
    
    except Exception as e:
        print(f"❌ Error getting recommendations: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'RecommendationsError',
            'message': str(e)
        }), 500


# ============================================
# GET RECOMMENDATIONS BY CATEGORY
# ============================================

@bp.route('/by-category/<category>', methods=['GET'])
def get_by_category(category):
    """
    Get all recommendations for a specific category
    
    Valid categories:
    - cafe
    - restaurant
    - tourist_spot
    - shopping
    - nightlife
    - cultural
    
    Example:
    GET /api/recommendations/by-category/cafe
    GET /api/recommendations/by-category/restaurant
    
    Response:
    {
        "category": "cafe",
        "total": 2,
        "recommendations": [...]
    }
    """
    try:
        print(f"🔍 Getting recommendations for category: {category}")
        
        valid_categories = ['cafe', 'restaurant', 'tourist_spot', 'shopping', 'nightlife', 'cultural']
        
        if category not in valid_categories:
            raise ValidationException(
                f"Invalid category '{category}'. Valid options: {', '.join(valid_categories)}",
                field='category'
            )
        
        recommendations = Recommendation.query.filter_by(
            category=category,
            is_active=True
        ).order_by(Recommendation.rating.desc()).all()
        
        print(f"✅ Found {len(recommendations)} recommendations")
        
        return jsonify({
            'category': category,
            'total': len(recommendations),
            'recommendations': [rec.to_dict() for rec in recommendations]
        }), 200
        
    except ValidationException as e:
        print(f"❌ Validation error: {e.message}")
        return jsonify(e.to_dict()), 400
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'CategoryError',
            'message': str(e)
        }), 500


# ============================================
# GET TOP RATED RECOMMENDATIONS
# ============================================

@bp.route('/top-rated', methods=['GET'])
def get_top_rated():
    """
    Get top-rated recommendations
    
    Query Parameters:
    - limit: number of results (default: 10, max: 50)
    - category: optional filter by category
    
    Example:
    GET /api/recommendations/top-rated
    GET /api/recommendations/top-rated?limit=5
    GET /api/recommendations/top-rated?limit=10&category=restaurant
    
    Response:
    {
        "total": 10,
        "recommendations": [...]
    }
    """
    try:
        print("🔍 Getting top-rated recommendations...")
        
        limit = request.args.get('limit', 10, type=int)
        category = request.args.get('category')
        
        if limit < 1 or limit > 50:
            raise ValidationException(
                "Limit must be between 1 and 50",
                field='limit'
            )
        
        query = Recommendation.query.filter_by(is_active=True)
        
        # Filter by category if provided
        if category:
            valid_categories = ['cafe', 'restaurant', 'tourist_spot', 'shopping', 'nightlife', 'cultural']
            if category not in valid_categories:
                raise ValidationException(f"Invalid category: {category}")
            query = query.filter_by(category=category)
        
        recommendations = query.order_by(
            Recommendation.rating.desc()
        ).limit(limit).all()
        
        print(f"✅ Found {len(recommendations)} top-rated recommendations")
        
        return jsonify({
            'total': len(recommendations),
            'limit': limit,
            'category_filter': category,
            'recommendations': [rec.to_dict() for rec in recommendations]
        }), 200
        
    except ValidationException as e:
        print(f"❌ Validation error: {e.message}")
        return jsonify(e.to_dict()), 400
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'TopRatedError',
            'message': str(e)
        }), 500


# ============================================
# GET SINGLE RECOMMENDATION
# ============================================

@bp.route('/<int:rec_id>', methods=['GET'])
def get_recommendation(rec_id):
    """
    Get details of a single recommendation
    
    Example:
    GET /api/recommendations/1
    
    Response:
    {
        "recommendation": {
            "recommendation_id": 1,
            "title": "Brew Haven Coffee Shop",
            ...
        }
    }
    """
    try:
        print(f"🔍 Getting recommendation ID: {rec_id}")
        
        rec = Recommendation.query.filter_by(
            recommendation_id=rec_id,
            is_active=True
        ).first()
        
        if not rec:
            raise ValidationException(
                f"Recommendation with ID {rec_id} not found"
            )
        
        print(f"✅ Found recommendation: {rec.title}")
        
        return jsonify({
            'recommendation': rec.to_dict()
        }), 200
        
    except ValidationException as e:
        print(f"❌ Not found: {e.message}")
        return jsonify(e.to_dict()), 404
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'RecommendationError',
            'message': str(e)
        }), 500


# ============================================
# GET ALL CATEGORIES (SUMMARY)
# ============================================

@bp.route('/categories', methods=['GET'])
def get_categories_summary():
    """
    Get summary of all recommendation categories
    Shows count of recommendations in each category
    
    Example:
    GET /api/recommendations/categories
    
    Response:
    {
        "categories": [
            {
                "category": "cafe",
                "count": 2,
                "avg_rating": 4.5
            },
            {
                "category": "restaurant",
                "count": 5,
                "avg_rating": 4.7
            },
            ...
        ]
    }
    """
    try:
        print("🔍 Getting category summary...")
        
        categories = ['cafe', 'restaurant', 'tourist_spot', 'shopping', 'nightlife', 'cultural']
        
        summary = []
        for cat in categories:
            recs = Recommendation.query.filter_by(
                category=cat,
                is_active=True
            ).all()
            
            if recs:
                avg_rating = sum(r.rating for r in recs) / len(recs)
                summary.append({
                    'category': cat,
                    'count': len(recs),
                    'avg_rating': round(avg_rating, 2)
                })
        
        print(f"✅ Found {len(summary)} categories with recommendations")
        
        return jsonify({
            'total_categories': len(summary),
            'categories': summary
        }), 200
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'CategoriesError',
            'message': str(e)
        }), 500


# ============================================
# SEARCH RECOMMENDATIONS (BY TEXT)
# ============================================

@bp.route('/search', methods=['GET'])
def search_recommendations():
    """
    Search recommendations by title or description
    
    Query Parameters:
    - q: search query (required)
    
    Example:
    GET /api/recommendations/search?q=coffee
    GET /api/recommendations/search?q=museum
    
    Response:
    {
        "query": "coffee",
        "total": 2,
        "recommendations": [...]
    }
    """
    try:
        query_text = request.args.get('q', '').strip()
        
        if not query_text:
            raise ValidationException(
                "Search query 'q' is required",
                field='q'
            )
        
        print(f"🔍 Searching for: {query_text}")
        
        # Search in title and description
        search_pattern = f"%{query_text}%"
        recommendations = Recommendation.query.filter(
            Recommendation.is_active == True,
            db.or_(
                Recommendation.title.ilike(search_pattern),
                Recommendation.description.ilike(search_pattern)
            )
        ).order_by(Recommendation.rating.desc()).all()
        
        print(f"✅ Found {len(recommendations)} results")
        
        return jsonify({
            'query': query_text,
            'total': len(recommendations),
            'recommendations': [rec.to_dict() for rec in recommendations]
        }), 200
        
    except ValidationException as e:
        print(f"❌ Validation error: {e.message}")
        return jsonify(e.to_dict()), 400
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'SearchError',
            'message': str(e)
        }), 500