/**
 * SCWS Google Reviews Widget
 * Fetches live ratings from Google Places API
 * 
 * Setup:
 * 1. Go to console.cloud.google.com
 * 2. Create a project (or use existing)
 * 3. Enable "Places API" 
 * 4. Create an API key (APIs & Services > Credentials)
 * 5. Restrict the key to your domain and Places API only
 * 6. Add your API key below
 */

const GOOGLE_REVIEWS_CONFIG = {
    // Add your Google Places API key here
    apiKey: 'YOUR_API_KEY_HERE',
    
    // Place IDs for your locations
    places: {
        ramona: 'ChIJnVbrUVH7_YARQO2fqNKjo40', // 1077 Main St, Ramona
        anza: 'ChIJj4LVzZgR24ARH4bwK2fOYc4'    // 57174 CA-371, Anza, CA 92539
    },
    
    // Display mode: 'highest', 'average', or 'both'
    displayMode: 'highest',
    
    // Cache duration in minutes (to reduce API calls)
    cacheDuration: 60
};

class GoogleReviewsWidget {
    constructor(config) {
        this.config = config;
        this.cache = this.loadCache();
    }

    loadCache() {
        try {
            const cached = localStorage.getItem('scws_reviews_cache');
            if (cached) {
                const data = JSON.parse(cached);
                if (Date.now() - data.timestamp < this.config.cacheDuration * 60 * 1000) {
                    return data;
                }
            }
        } catch (e) {
            console.log('Cache not available');
        }
        return null;
    }

    saveCache(data) {
        try {
            localStorage.setItem('scws_reviews_cache', JSON.stringify({
                ...data,
                timestamp: Date.now()
            }));
        } catch (e) {
            console.log('Could not save cache');
        }
    }

    async fetchPlaceDetails(placeId) {
        const url = `https://maps.googleapis.com/maps/api/place/details/json?place_id=${placeId}&fields=rating,user_ratings_total,reviews&key=${this.config.apiKey}`;
        
        // Note: Direct API calls from browser will be blocked by CORS
        // You'll need to use a proxy or the Places Library
        // For now, we'll use the Google Maps JavaScript API
        
        return new Promise((resolve, reject) => {
            if (!window.google || !window.google.maps) {
                reject(new Error('Google Maps API not loaded'));
                return;
            }

            const service = new google.maps.places.PlacesService(
                document.createElement('div')
            );

            service.getDetails(
                {
                    placeId: placeId,
                    fields: ['rating', 'user_ratings_total', 'reviews']
                },
                (place, status) => {
                    if (status === google.maps.places.PlacesServiceStatus.OK) {
                        resolve({
                            rating: place.rating,
                            totalReviews: place.user_ratings_total,
                            reviews: place.reviews || []
                        });
                    } else {
                        reject(new Error(`Places API error: ${status}`));
                    }
                }
            );
        });
    }

    async getReviews() {
        // Return cached data if available
        if (this.cache && this.cache.places) {
            return this.cache.places;
        }

        try {
            const [ramona, anza] = await Promise.all([
                this.fetchPlaceDetails(this.config.places.ramona),
                this.fetchPlaceDetails(this.config.places.anza)
            ]);

            const data = { ramona, anza };
            this.saveCache({ places: data });
            return data;
        } catch (error) {
            console.error('Error fetching reviews:', error);
            // Return fallback data
            return {
                ramona: { rating: 4.7, totalReviews: 56 },
                anza: { rating: 4.9, totalReviews: 52 }
            };
        }
    }

    async render() {
        const data = await this.getReviews();
        
        let displayRating, displayText;
        
        if (this.config.displayMode === 'highest') {
            displayRating = Math.max(data.ramona.rating, data.anza.rating);
            displayText = 'on Google';
        } else if (this.config.displayMode === 'average') {
            const totalReviews = data.ramona.totalReviews + data.anza.totalReviews;
            displayRating = (
                (data.ramona.rating * data.ramona.totalReviews + 
                 data.anza.rating * data.anza.totalReviews) / totalReviews
            ).toFixed(1);
            displayText = `(${totalReviews} reviews)`;
        } else {
            // Both
            displayRating = `${data.ramona.rating}/${data.anza.rating}`;
            displayText = 'Ramona/Anza';
        }

        // Update all elements with data-reviews-rating class
        document.querySelectorAll('[data-reviews-rating]').forEach(el => {
            el.textContent = displayRating;
        });

        document.querySelectorAll('[data-reviews-text]').forEach(el => {
            el.textContent = displayText;
        });

        document.querySelectorAll('[data-reviews-count]').forEach(el => {
            const total = data.ramona.totalReviews + data.anza.totalReviews;
            el.textContent = `${total} reviews`;
        });

        return data;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (GOOGLE_REVIEWS_CONFIG.apiKey !== 'YOUR_API_KEY_HERE') {
        const widget = new GoogleReviewsWidget(GOOGLE_REVIEWS_CONFIG);
        widget.render();
    } else {
        console.log('Google Reviews Widget: Add your API key to enable live reviews');
    }
});

// Export for use elsewhere
window.GoogleReviewsWidget = GoogleReviewsWidget;
window.GOOGLE_REVIEWS_CONFIG = GOOGLE_REVIEWS_CONFIG;
