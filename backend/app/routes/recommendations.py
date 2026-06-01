"""
Recommendations Routes
Handles retrieval of travel recommendations
Simplified version containing only essential routes and fields.
"""

from flask import Blueprint, request, jsonify
from app import db
from app.models import Recommendation
from app.utils.exceptions import ValidationException
import traceback

bp = Blueprint('recommendations', __name__)


# ============================================
# GET ALL RECOMMENDATIONS
# ============================================

@bp.route('', methods=['GET'])
def get_recommendations():
    """
    Get all recommendations
    
    Response:
    {
        "total": 8,
        "recommendations": [
            {
                "recommendation_id": 1,
                "title": "Lalbagh Botanical Garden",
                "description": "A sprawling garden situated in a 240 acres piece of land in the heart of the city, Lalbagh houses India’s largest collection of tropical plants and sub-tropical plants, including trees that are several centuries old",
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Glasshouse_and_fountain_at_lalbagh.jpg/500px-Glasshouse_and_fountain_at_lalbagh.jpg",
                "google_maps_url": "https://www.bing.com/ck/a?!&&p=a07c5fadd797e223960f0d75a8df5eab17ed0215860016181dcf38bff6be3524JmltdHM9MTc4MDI3MjAwMA&ptn=3&ver=2&hsh=4&fclid=007da303-de0b-67c6-3f75-b061dfa66662&u=a1L21hcHM_Jm1lcGk9MH5-RW1iZWRkZWR-QWRkcmVzc19MaW5rJnR5PTE4JnE9TGFsYmFnaCUyMEJvdGFuaWNhbCUyMEdhcmRlbiZzcz15cGlkLllONDA3MHgxNjIyOTQyMjM0MzIwMTE2MDAzMSZwcG9pcz0xMi45Mzc5MDA1NDMyMTI4OV83Ny41ODAyOTkzNzc0NDE0X0xhbGJhZ2glMjBCb3RhbmljYWwlMjBHYXJkZW5fWU40MDcweDE2MjI5NDIyMzQzMjAxMTYwMDMxfiZjcD0xMi45Mzc5MDF-NzcuNTgwMjk5JnY9MiZzVj0xJkZPUk09TVBTUlBM"
            },
            ...
        ]
    }
    """
    try:
        print("🔍 Getting all recommendations...")
        recommendations = Recommendation.query.all()
        print(f"✅ Found {len(recommendations)} recommendations")
        
        return jsonify({
            'total': len(recommendations),
            'recommendations': [rec.to_dict() for rec in recommendations]
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting recommendations: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'RecommendationsError',
            'message': str(e)
        }), 500


# ============================================
# GET SINGLE RECOMMENDATION
# ============================================

@bp.route('/<int:rec_id>', methods=['GET'])
def get_recommendation(rec_id):
    """
    Get details of a single recommendation
    """
    try:
        print(f"🔍 Getting recommendation ID: {rec_id}")
        rec = Recommendation.query.get(rec_id)
        
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
# SEARCH RECOMMENDATIONS
# ============================================

@bp.route('/search', methods=['GET'])
def search_recommendations():
    """
    Search recommendations by title or description
    """
    try:
        query_text = request.args.get('q', '').strip()
        
        if not query_text:
            raise ValidationException(
                "Search query 'q' is required",
                field='q'
            )
        
        print(f"🔍 Searching for: {query_text}")
        
        search_pattern = f"%{query_text}%"
        recommendations = Recommendation.query.filter(
            db.or_(
                Recommendation.title.ilike(search_pattern),
                Recommendation.description.ilike(search_pattern)
            )
        ).all()
        
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