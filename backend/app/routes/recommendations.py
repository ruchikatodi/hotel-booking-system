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
                "description": "...",
                "image_url": "...",
                "google_maps_url": "..."
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