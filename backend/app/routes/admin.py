"""
Admin Routes
Analytics dashboard with Pandas, NumPy, and Matplotlib
"""

from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Booking, Payment, Room, RoomCategory, LoyaltyPoints
from app.utils.exceptions import AuthorizationException
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, date, timedelta
import io
import base64
import traceback

bp = Blueprint('admin', __name__)


def check_admin(user_id):
    """Check if user is admin"""
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        raise AuthorizationException("Admin access required")
    return user


# ============== REVENUE ANALYTICS ==============
def compute_revenue_analytics(period="monthly", days=90):
    start_date = date.today() - timedelta(days=days)

    bookings = Booking.query.filter(
        Booking.booking_date >= start_date,
        Booking.status.in_(['confirmed', 'checked_in', 'checked_out'])
    ).all()

    if not bookings:
        return {
            'total_revenue': 0.0,
            'total_bookings': 0,
            'average_booking_value': 0.0,
            'std_booking_value': 0.0,
            'min_booking_value': 0.0,
            'max_booking_value': 0.0,
            'revenue_by_period': {},
            'growth_rate': 0.0,
            'period': period,
            'days_analyzed': days
        }

    data = [{
        'booking_date': b.booking_date,
        'total_amount': b.total_amount
    } for b in bookings]

    df = pd.DataFrame(data)
    df['booking_date'] = pd.to_datetime(df['booking_date'])

    total_revenue = float(df['total_amount'].sum())
    mean_value = float(df['total_amount'].mean())
    std_value = float(df['total_amount'].std())
    min_value = float(df['total_amount'].min())
    max_value = float(df['total_amount'].max())

    # Determine grouping period
    if period == 'daily':
        df['period'] = df['booking_date'].dt.date
    elif period == 'weekly':
        df['period'] = df['booking_date'].dt.to_period('W')
    else:
        df['period'] = df['booking_date'].dt.to_period('M')

    # Revenue by period
    #revenue_by_period = df.groupby('period')['total_amount'].agg(['sum', 'count']).to_dict()
    grouped = df.groupby('period')['total_amount'].agg(['sum', 'count'])
    # Convert PeriodIndex to plain strings
    grouped.index = grouped.index.astype(str)
    revenue_by_period = grouped.to_dict()

    # Growth rate
    period_revenues = df.groupby('period')['total_amount'].sum().values
    if len(period_revenues) > 1:
        growth_rates = np.diff(period_revenues) / period_revenues[:-1] * 100
        growth_rate = float(np.mean(growth_rates))
    else:
        growth_rate = 0.0

    return {
        'total_revenue': total_revenue,
        'total_bookings': len(bookings),
        'average_booking_value': mean_value,
        'std_booking_value': std_value,
        'min_booking_value': min_value,
        'max_booking_value': max_value,
        'revenue_by_period': revenue_by_period,
        'growth_rate': growth_rate,
        'period': period,
        'days_analyzed': days
    }


@bp.route('/analytics/revenue', methods=['GET'])
@jwt_required()
def revenue_analytics():
    """
    Get revenue analytics
    
    Requires: Admin access
    
    Query Parameters (optional):
    - period: 'daily', 'weekly', 'monthly' (default: 'monthly')
    - days: Number of days to analyze (default: 90)
    
    Response:
    {
        "total_revenue": 5000.0,
        "total_bookings": 10,
        "average_booking_value": 500.0,
        "revenue_by_period": { ... },
        "growth_rate": 5.2
    }
    """

    try:
        user_id = get_jwt_identity()
        check_admin(user_id)

        period = request.args.get('period', 'monthly')
        days = request.args.get('days', 90, type=int)

        data = compute_revenue_analytics(period, days)
        return jsonify(data), 200

    except AuthorizationException as e:
        return jsonify(e.to_dict()), 403
    except Exception as e:
        print("❌ Revenue analytics error:", str(e))
        traceback.print_exc()
        return jsonify({'error': 'AnalyticsError', 'message': str(e)}), 500


    # try:
    #     user_id = get_jwt_identity()
    #     check_admin(user_id)
        
    #     period = request.args.get('period', 'monthly')
    #     days = request.args.get('days', 90, type=int)
        
    #     # Get bookings data
    #     start_date = date.today() - timedelta(days=days)
        
    #     bookings = Booking.query.filter(
    #         Booking.booking_date >= start_date,
    #         Booking.status.in_(['confirmed', 'checked_in', 'checked_out'])
    #     ).all()
        
    #     if not bookings:
    #         return jsonify({
    #             'total_revenue': 0.0,
    #             'total_bookings': 0,
    #             'average_booking_value': 0.0,
    #             'revenue_by_period': {},
    #             'growth_rate': 0.0
    #         }), 200
        
    #     # Convert to DataFrame
    #     data = []
    #     for booking in bookings:
    #         data.append({
    #             'booking_date': booking.booking_date,
    #             'total_amount': booking.total_amount
    #         })
        
    #     df = pd.DataFrame(data)
    #     df['booking_date'] = pd.to_datetime(df['booking_date'])
        
    #     # Calculate statistics using NumPy
    #     total_revenue = np.sum(df['total_amount'].values)
    #     mean_value = np.mean(df['total_amount'].values)
    #     std_value = np.std(df['total_amount'].values)
        
    #     # Group by period
    #     if period == 'daily':
    #         df['period'] = df['booking_date'].dt.date
    #     elif period == 'weekly':
    #         df['period'] = df['booking_date'].dt.to_period('W')
    #     else:  # monthly
    #         df['period'] = df['booking_date'].dt.to_period('M')
        
    #     revenue_by_period = df.groupby('period')['total_amount'].agg(['sum', 'count']).to_dict()
        
    #     # Calculate growth rate
    #     period_revenues = df.groupby('period')['total_amount'].sum().values
    #     if len(period_revenues) > 1:
    #         growth_rates = np.diff(period_revenues) / period_revenues[:-1] * 100
    #         growth_rate = float(np.mean(growth_rates))
    #     else:
    #         growth_rate = 0.0
        
    #     return jsonify({
    #         'total_revenue': float(total_revenue),
    #         'total_bookings': len(bookings),
    #         'average_booking_value': float(mean_value),
    #         'std_booking_value': float(std_value),
    #         'min_booking_value': float(np.min(df['total_amount'].values)),
    #         'max_booking_value': float(np.max(df['total_amount'].values)),
    #         'growth_rate': growth_rate,
    #         'period': period,
    #         'days_analyzed': days
    #     }), 200
        
    # except AuthorizationException as e:
    #     return jsonify(e.to_dict()), 403
    # except Exception as e:
    #     print(f"❌ Revenue analytics error: {str(e)}")
    #     traceback.print_exc()
    #     return jsonify({
    #         'error': 'AnalyticsError',
    #         'message': str(e)
    #     }), 500


def compute_occupancy_analytics(days=30):
    total_rooms = Room.query.count()

    start_date = date.today() - timedelta(days=days)
    end_date = date.today()

    # Get active bookings
    bookings = Booking.query.filter(
        Booking.status.in_(['confirmed', 'checked_in', 'checked_out']),
        Booking.check_in_date <= end_date,
        Booking.check_out_date >= start_date
    ).all()

    # Daily occupancy calculation
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    daily_occupancy = []

    for current_date in date_range:
        occupied = 0

        for booking in bookings:
            if booking.check_in_date <= current_date.date() < booking.check_out_date:
                occupied += 1

        occupancy_rate = (occupied / total_rooms * 100) if total_rooms > 0 else 0

        daily_occupancy.append({
            "date": current_date.date().isoformat(),
            "occupancy_rate": occupancy_rate,
            "rooms_occupied": occupied
        })

    occupancy_rates = [d["occupancy_rate"] for d in daily_occupancy]
    rooms_occupied_list = [d["rooms_occupied"] for d in daily_occupancy]

    return {
        "overall_occupancy_rate": float(np.mean(occupancy_rates)) if occupancy_rates else 0.0,
        "peak_occupancy": float(np.max(occupancy_rates)) if occupancy_rates else 0.0,
        "lowest_occupancy": float(np.min(occupancy_rates)) if occupancy_rates else 0.0,
        "total_rooms": total_rooms,
        "average_rooms_occupied": float(np.mean(rooms_occupied_list)) if rooms_occupied_list else 0.0,
        "daily_occupancy": daily_occupancy,
        "days_analyzed": days
    }

@bp.route('/analytics/occupancy', methods=['GET'])
@jwt_required()
def occupancy_analytics():
    try:
        user_id = get_jwt_identity()
        check_admin(user_id)

        days = request.args.get('days', 30, type=int)

        data = compute_occupancy_analytics(days)
        return jsonify(data), 200

    except AuthorizationException as e:
        return jsonify(e.to_dict()), 403
    except Exception as e:
        print("❌ Occupancy analytics error:", str(e))
        traceback.print_exc()
        return jsonify({
            "error": "AnalyticsError",
            "message": str(e)
        }), 500


# ============== OCCUPANCY ANALYTICS ==============
# @bp.route('/analytics/occupancy', methods=['GET'])
# @jwt_required()
# def occupancy_analytics():
#     """
#     Get occupancy rate and statistics
    
#     Requires: Admin access
    
#     Query Parameters (optional):
#     - days: Number of days to analyze (default: 30)
    
#     Response:
#     {
#         "overall_occupancy_rate": 75.5,
#         "total_rooms": 8,
#         "booked_rooms": 6,
#         "daily_occupancy": [ ... ],
#         "peak_occupancy": 100.0,
#         "lowest_occupancy": 0.0
#     }
#     """
#     try:
#         user_id = get_jwt_identity()
#         check_admin(user_id)
        
#         days = request.args.get('days', 30, type=int)
        
#         # Get total rooms
#         total_rooms = Room.query.count()
        
#         # Get date range
#         start_date = date.today() - timedelta(days=days)
#         end_date = date.today()
        
#         # Get active bookings
#         bookings = Booking.query.filter(
#             Booking.status.in_(['confirmed', 'checked_in', 'checked_out']),
#             Booking.check_in_date <= end_date,
#             Booking.check_out_date >= start_date
#         ).all()
        
#         # Calculate daily occupancy
#         date_range = pd.date_range(start=start_date, end=end_date, freq='D')
#         daily_occupancy = []
        
#         for current_date in date_range:
#             occupied = 0
#             for booking in bookings:
#                 if booking.check_in_date <= current_date.date() < booking.check_out_date:
#                     occupied += 1
            
#             occupancy_rate = (occupied / total_rooms * 100) if total_rooms > 0 else 0
#             daily_occupancy.append({
#                 'date': current_date.date().isoformat(),
#                 'occupancy_rate': occupancy_rate,
#                 'rooms_occupied': occupied
#             })
        
#         # Calculate statistics
#         occupancy_rates = [d['occupancy_rate'] for d in daily_occupancy]
        
#         return jsonify({
#             'overall_occupancy_rate': float(np.mean(occupancy_rates)) if occupancy_rates else 0.0,
#             'peak_occupancy': float(np.max(occupancy_rates)) if occupancy_rates else 0.0,
#             'lowest_occupancy': float(np.min(occupancy_rates)) if occupancy_rates else 0.0,
#             'total_rooms': total_rooms,
#             'average_rooms_occupied': float(np.mean([d['rooms_occupied'] for d in daily_occupancy])) if daily_occupancy else 0.0,
#             'daily_occupancy': daily_occupancy,
#             'days_analyzed': days
#         }), 200
        
#     except AuthorizationException as e:
#         return jsonify(e.to_dict()), 403
#     except Exception as e:
#         print(f"❌ Occupancy analytics error: {str(e)}")
#         traceback.print_exc()
#         return jsonify({
#             'error': 'AnalyticsError',
#             'message': str(e)
#         }), 500


# ============== ROOM PERFORMANCE ==============
# @bp.route('/analytics/room-performance', methods=['GET'])
# @jwt_required()
# def room_performance():
#     """
#     Get performance statistics by room category
    
#     Requires: Admin access
    
#     Response:
#     {
#         "room_performance": [
#             {
#                 "category_name": "Standard Room",
#                 "total_bookings": 10,
#                 "total_revenue": 1000.0,
#                 "average_occupancy": 75.0,
#                 "avg_rating": 4.5
#             },
#             ...
#         ]
#     }
#     """
#     try:
#         user_id = get_jwt_identity()
#         check_admin(user_id)
        
#         # Get categories with their bookings
#         categories = RoomCategory.query.all()
#         performance = []
        
#         for category in categories:
#             # Get bookings for this category
#             bookings = db.session.query(Booking).join(
#                 Room, Booking.room_id == Room.room_id
#             ).filter(
#                 Room.category_id == category.category_id,
#                 Booking.status.in_(['confirmed', 'checked_in', 'checked_out'])
#             ).all()
            
#             if not bookings:
#                 performance.append({
#                     'category_id': category.category_id,
#                     'category_name': category.name,
#                     'total_bookings': 0,
#                     'total_revenue': 0.0,
#                     'average_booking_value': 0.0,
#                     'total_nights_booked': 0,
#                     'base_price': category.base_price,
#                     'capacity': category.capacity
#                 })
#                 continue
            
#             # Calculate statistics
#             total_revenue = sum(b.total_amount for b in bookings)
#             total_nights = sum(b.nights for b in bookings)
#             avg_value = total_revenue / len(bookings) if bookings else 0
            
#             performance.append({
#                 'category_id': category.category_id,
#                 'category_name': category.name,
#                 'total_bookings': len(bookings),
#                 'total_revenue': float(total_revenue),
#                 'average_booking_value': float(avg_value),
#                 'total_nights_booked': total_nights,
#                 'base_price': category.base_price,
#                 'capacity': category.capacity,
#                 'revenue_per_night': float(total_revenue / total_nights) if total_nights > 0 else 0.0
#             })
        
#         return jsonify({
#             'room_performance': performance
#         }), 200
        
#     except AuthorizationException as e:
#         return jsonify(e.to_dict()), 403
#     except Exception as e:
#         print(f"❌ Room performance error: {str(e)}")
#         traceback.print_exc()
#         return jsonify({
#             'error': 'AnalyticsError',
#             'message': str(e)
#         }), 500

def compute_room_performance():
    categories = RoomCategory.query.all()
    performance = []

    for category in categories:
        bookings = (
            db.session.query(Booking)
            .join(Room, Booking.room_id == Room.room_id)
            .filter(
                Room.category_id == category.category_id,
                Booking.status.in_(['confirmed', 'checked_in', 'checked_out'])
            )
            .all()
        )

        if not bookings:
            performance.append({
                'category_id': category.category_id,
                'category_name': category.name,
                'total_bookings': 0,
                'total_revenue': 0.0,
                'average_booking_value': 0.0,
                'total_nights_booked': 0,
                'base_price': float(category.base_price),
                'capacity': category.capacity,
                'revenue_per_night': 0.0
            })
            continue

        total_revenue = sum(b.total_amount for b in bookings)
        total_nights = sum(b.nights for b in bookings)
        avg_value = total_revenue / len(bookings) if bookings else 0

        performance.append({
            'category_id': category.category_id,
            'category_name': category.name,
            'total_bookings': len(bookings),
            'total_revenue': float(total_revenue),
            'average_booking_value': float(avg_value),
            'total_nights_booked': total_nights,
            'base_price': float(category.base_price),
            'capacity': category.capacity,
            'revenue_per_night': float(total_revenue / total_nights) if total_nights else 0.0
        })

    return {
        "room_performance": performance
    }

@bp.route('/analytics/room-performance', methods=['GET'])
@jwt_required()
def room_performance():
    """
    Returns room category performance analytics.
    Admin only.
    """
    try:
        user_id = get_jwt_identity()
        check_admin(user_id)

        data = compute_room_performance()
        return jsonify(data), 200

    except AuthorizationException as e:
        return jsonify(e.to_dict()), 403
    except Exception as e:
        print(f"❌ Room performance error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "error": "AnalyticsError",
            "message": str(e)
        }), 500


# ============== CUSTOMER ANALYTICS ==============
# @bp.route('/analytics/customers', methods=['GET'])
# @jwt_required()
# def customer_analytics():
#     """
#     Get customer insights and segmentation
    
#     Requires: Admin access
    
#     Response:
#     {
#         "total_customers": 50,
#         "repeat_customers": 15,
#         "repeat_rate": 30.0,
#         "average_ltv": 2500.0,
#         "customer_segments": { ... }
#     }
#     """
#     try:
#         user_id = get_jwt_identity()
#         check_admin(user_id)
        
#         # Get all customers
#         customers = User.query.filter_by(role='customer').all()
#         total_customers = len(customers)
        
#         customer_stats = []
        
#         for customer in customers:
#             bookings = Booking.query.filter_by(user_id=customer.user_id).all()
#             total_spent = sum(b.total_amount for b in bookings if b.status in ['confirmed', 'checked_in', 'checked_out'])
            
#             customer_stats.append({
#                 'user_id': customer.user_id,
#                 'total_bookings': len(bookings),
#                 'total_spent': total_spent
#             })
        
#         # Segment customers using NumPy
#         spent_values = np.array([cs['total_spent'] for cs in customer_stats])
        
#         if len(spent_values) > 0:
#             percentiles = np.percentile(spent_values, [25, 50, 75])
            
#             segments = {'high_value': 0, 'medium_value': 0, 'low_value': 0, 'new': 0}
            
#             for cs in customer_stats:
#                 if cs['total_bookings'] == 0:
#                     segments['new'] += 1
#                 elif cs['total_spent'] >= percentiles[2]:
#                     segments['high_value'] += 1
#                 elif cs['total_spent'] >= percentiles[1]:
#                     segments['medium_value'] += 1
#                 else:
#                     segments['low_value'] += 1
            
#             repeat_customers = sum(1 for cs in customer_stats if cs['total_bookings'] > 1)
#             repeat_rate = (repeat_customers / total_customers * 100) if total_customers > 0 else 0
#             avg_ltv = float(np.mean(spent_values)) if len(spent_values) > 0 else 0.0
#         else:
#             segments = {'high_value': 0, 'medium_value': 0, 'low_value': 0, 'new': 0}
#             repeat_customers = 0
#             repeat_rate = 0.0
#             avg_ltv = 0.0
        
#         return jsonify({
#             'total_customers': total_customers,
#             'repeat_customers': repeat_customers,
#             'repeat_rate': repeat_rate,
#             'average_ltv': avg_ltv,
#             'customer_segments': segments
#         }), 200
        
#     except AuthorizationException as e:
#         return jsonify(e.to_dict()), 403
#     except Exception as e:
#         print(f"❌ Customer analytics error: {str(e)}")
#         traceback.print_exc()
#         return jsonify({
#             'error': 'AnalyticsError',
#             'message': str(e)
#         }), 500

def compute_customer_analytics():
    # Get all customers
    customers = User.query.filter_by(role='customer').all()
    total_customers = len(customers)
    
    customer_stats = []
    
    for customer in customers:
        bookings = Booking.query.filter_by(user_id=customer.user_id).all()
        total_spent = sum(
            b.total_amount for b in bookings 
            if b.status in ['confirmed', 'checked_in', 'checked_out']
        )
        
        customer_stats.append({
            'user_id': customer.user_id,
            'total_bookings': len(bookings),
            'total_spent': total_spent
        })
    
    spent_values = np.array([cs['total_spent'] for cs in customer_stats])
    
    if len(spent_values) > 0:
        percentiles = np.percentile(spent_values, [25, 50, 75])
        
        segments = {
            'high_value': 0,
            'medium_value': 0,
            'low_value': 0,
            'new': 0
        }
        
        for cs in customer_stats:
            if cs['total_bookings'] == 0:
                segments['new'] += 1
            elif cs['total_spent'] >= percentiles[2]:
                segments['high_value'] += 1
            elif cs['total_spent'] >= percentiles[1]:
                segments['medium_value'] += 1
            else:
                segments['low_value'] += 1
        
        repeat_customers = sum(1 for cs in customer_stats if cs['total_bookings'] > 1)
        repeat_rate = (repeat_customers / total_customers * 100) if total_customers else 0
        avg_ltv = float(np.mean(spent_values))
    else:
        segments = {
            'high_value': 0,
            'medium_value': 0,
            'low_value': 0,
            'new': 0
        }
        repeat_customers = 0
        repeat_rate = 0.0
        avg_ltv = 0.0
    
    return {
        'total_customers': total_customers,
        'repeat_customers': repeat_customers,
        'repeat_rate': repeat_rate,
        'average_ltv': avg_ltv,
        'customer_segments': segments
    }

@bp.route('/analytics/customers', methods=['GET'])
@jwt_required()
def customer_analytics():
    try:
        user_id = get_jwt_identity()
        check_admin(user_id)

        return jsonify(compute_customer_analytics()), 200

    except AuthorizationException as e:
        return jsonify(e.to_dict()), 403
    except Exception as e:
        print(f"❌ Customer analytics error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'AnalyticsError',
            'message': str(e)
        }), 500


# ============== COMPLETE DASHBOARD ==============
# @bp.route('/dashboard', methods=['GET'])
# @jwt_required()
# def dashboard():
#     """
#     Get complete admin dashboard data
    
#     Requires: Admin access
    
#     Response: All analytics combined
#     """
#     try:
#         user_id = get_jwt_identity()
#         check_admin(user_id)
        
#         # Get all analytics
#         revenue = revenue_analytics()
#         occupancy = occupancy_analytics()
#         performance = room_performance()
#         customers = customer_analytics()
        
#         # Parse JSON responses
#         revenue_data = revenue.get_json() if hasattr(revenue, 'get_json') else revenue[0]
#         occupancy_data = occupancy.get_json() if hasattr(occupancy, 'get_json') else occupancy[0]
#         performance_data = performance.get_json() if hasattr(performance, 'get_json') else performance[0]
#         customers_data = customers.get_json() if hasattr(customers, 'get_json') else customers[0]
        
#         return jsonify({
#             'generated_at': datetime.now().isoformat(),
#             'revenue': revenue_data,
#             'occupancy': occupancy_data,
#             'room_performance': performance_data,
#             'customers': customers_data
#         }), 200
        
#     except AuthorizationException as e:
#         return jsonify(e.to_dict()), 403
#     except Exception as e:
#         print(f"❌ Dashboard error: {str(e)}")
#         traceback.print_exc()
#         return jsonify({
#             'error': 'DashboardError',
#             'message': str(e)
#         }), 500

@bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    try:
        user_id = get_jwt_identity()
        check_admin(user_id)

        revenue_data = compute_revenue_analytics()
        occupancy_data = compute_occupancy_analytics()
        performance_data = compute_room_performance()
        customers_data = compute_customer_analytics()

        return jsonify({
            "generated_at": datetime.now().isoformat(),
            "revenue": revenue_data,
            "occupancy": occupancy_data,
            "room_performance": performance_data,
            "customers": customers_data
        }), 200

    except AuthorizationException as e:
        return jsonify(e.to_dict()), 403
    except Exception as e:
        print("❌ Dashboard error:", e)
        traceback.print_exc()
        return jsonify({"error": "DashboardError", "message": str(e)}), 500


# ============== BOOKING MANAGEMENT ==============
# @bp.route('/bookings', methods=['GET'])
# @jwt_required()
# def get_all_bookings():
#     """
#     Get all bookings (admin view)
    
#     Requires: Admin access
    
#     Query Parameters (optional):
#     - status: Filter by status
#     - user_id: Filter by user
    
#     Response: All bookings with details
#     """
#     try:
#         user_id = get_jwt_identity()
#         check_admin(user_id)
        
#         query = Booking.query
        
#         status = request.args.get('status')
#         if status:
#             query = query.filter_by(status=status)
        
#         user_filter = request.args.get('user_id', type=int)
#         if user_filter:
#             query = query.filter_by(user_id=user_filter)
        
#         bookings = query.order_by(Booking.booking_date.desc()).all()
#         bookings_data = [b.to_dict(include_payment=True) for b in bookings]
        
#         return jsonify({
#             'total_bookings': len(bookings_data),
#             'bookings': bookings_data
#         }), 200
        
#     except AuthorizationException as e:
#         return jsonify(e.to_dict()), 403
#     except Exception as e:
#         print(f"❌ Get bookings error: {str(e)}")
#         return jsonify({
#             'error': 'Error',
#             'message': str(e)
#         }), 500
def compute_all_bookings(status=None, user_id=None):
    """
    Compute function for retrieving all bookings.
    Pure Python — no Flask request/response here.
    """

    query = Booking.query

    if status:
        query = query.filter_by(status=status)

    if user_id:
        query = query.filter_by(user_id=user_id)

    bookings = query.order_by(Booking.booking_date.desc()).all()

    return {
        "total_bookings": len(bookings),
        "bookings": [b.to_dict(include_payment=True) for b in bookings]
    }
@bp.route('/bookings', methods=['GET'])
@jwt_required()
def get_all_bookings():
    """
    Get all bookings (admin view)
    """
    try:
        user_id = get_jwt_identity()
        check_admin(user_id)

        status = request.args.get('status')
        user_filter = request.args.get('user_id', type=int)

        data = compute_all_bookings(status=status, user_id=user_filter)

        return jsonify(data), 200

    except AuthorizationException as e:
        return jsonify(e.to_dict()), 403
    except Exception as e:
        print(f"❌ Get bookings error: {str(e)}")
        return jsonify({
            'error': 'Error',
            'message': str(e)
        }), 500


@bp.route('/bookings/<int:booking_id>/status', methods=['PATCH'])
@jwt_required()
def update_booking_status(booking_id):
    """Confirm, cancel, check in, or check out a booking from admin."""
    try:
        user_id = get_jwt_identity()
        check_admin(user_id)

        data = request.get_json() or {}
        status = data.get('status')
        valid_statuses = ['pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled']

        if status not in valid_statuses:
            return jsonify({'error': 'ValidationError', 'message': 'Invalid booking status'}), 400

        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({'error': 'NotFound', 'message': 'Booking not found'}), 404

        booking.status = status
        if status == 'cancelled':
            booking.cancellation_reason = data.get('reason', 'Cancelled by admin')
            booking.cancelled_at = datetime.utcnow()
            if booking.room:
                booking.room.status = 'available'
        elif status in ['confirmed', 'checked_in']:
            if booking.room:
                booking.room.status = 'reserved'
        elif status == 'checked_out':
            if booking.room:
                booking.room.status = 'available'

        db.session.commit()
        return jsonify({'message': 'Booking updated', 'booking': booking.to_dict(include_payment=True)}), 200

    except AuthorizationException as e:
        db.session.rollback()
        return jsonify(e.to_dict()), 403
    except Exception as e:
        db.session.rollback()
        print(f"âŒ Update booking status error: {str(e)}")
        return jsonify({'error': 'Error', 'message': str(e)}), 500


@bp.route('/rooms', methods=['GET'])
@jwt_required()
def admin_rooms():
    """List rooms with category details."""
    try:
        user_id = get_jwt_identity()
        check_admin(user_id)

        rooms = Room.query.order_by(Room.room_number.asc()).all()
        return jsonify({
            'total_rooms': len(rooms),
            'rooms': [room.to_dict(include_category=True) for room in rooms]
        }), 200

    except AuthorizationException as e:
        return jsonify(e.to_dict()), 403
    except Exception as e:
        return jsonify({'error': 'Error', 'message': str(e)}), 500


@bp.route('/rooms', methods=['POST'])
@jwt_required()
def add_room():
    """Add a room to an existing category."""
    try:
        user_id = get_jwt_identity()
        check_admin(user_id)

        data = request.get_json() or {}
        required = ['room_number', 'category_id', 'floor']
        if any(field not in data for field in required):
            return jsonify({'error': 'ValidationError', 'message': 'room_number, category_id, and floor are required'}), 400

        if Room.query.filter_by(room_number=data['room_number']).first():
            return jsonify({'error': 'ValidationError', 'message': 'Room number already exists'}), 400

        room = Room(
            room_number=data['room_number'],
            category_id=int(data['category_id']),
            floor=int(data['floor']),
            status=data.get('status', 'available'),
            description=data.get('description', '')
        )
        db.session.add(room)
        db.session.commit()
        return jsonify({'message': 'Room added', 'room': room.to_dict(include_category=True)}), 201

    except AuthorizationException as e:
        db.session.rollback()
        return jsonify(e.to_dict()), 403
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error', 'message': str(e)}), 500


@bp.route('/rooms/<int:room_id>', methods=['PATCH'])
@jwt_required()
def update_room(room_id):
    """Edit room details, status, or price through its category."""
    try:
        user_id = get_jwt_identity()
        check_admin(user_id)

        data = request.get_json() or {}
        room = Room.query.get(room_id)
        if not room:
            return jsonify({'error': 'NotFound', 'message': 'Room not found'}), 404

        if 'room_number' in data:
            room.room_number = data['room_number']
        if 'floor' in data:
            room.floor = int(data['floor'])
        if 'status' in data:
            room.set_status(data['status'])
        if 'description' in data:
            room.description = data['description']
        if 'base_price' in data and room.category:
            room.category.base_price = float(data['base_price'])
        if 'category_description' in data and room.category:
            room.category.description = data['category_description']
        if 'amenities' in data and room.category:
            amenities = data['amenities']
            room.category.amenities = ', '.join(amenities) if isinstance(amenities, list) else amenities

        db.session.commit()
        return jsonify({'message': 'Room updated', 'room': room.to_dict(include_category=True)}), 200

    except AuthorizationException as e:
        db.session.rollback()
        return jsonify(e.to_dict()), 403
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error', 'message': str(e)}), 500


@bp.route('/customers', methods=['GET'])
@jwt_required()
def admin_customers():
    """List guests with booking history and loyalty data."""
    try:
        user_id = get_jwt_identity()
        check_admin(user_id)

        customers = User.query.filter_by(role='customer').order_by(User.created_at.desc()).all()
        data = []
        for customer in customers:
            customer_data = customer.to_dict()
            customer_data['bookings'] = [b.to_dict(include_payment=True) for b in customer.bookings]
            customer_data['loyalty'] = customer.loyalty.to_dict() if customer.loyalty else None
            data.append(customer_data)

        return jsonify({'total_customers': len(data), 'customers': data}), 200

    except AuthorizationException as e:
        return jsonify(e.to_dict()), 403
    except Exception as e:
        return jsonify({'error': 'Error', 'message': str(e)}), 500

