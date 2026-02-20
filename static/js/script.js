// Cart Management
document.addEventListener('DOMContentLoaded', function() {
    setupAlertClosers();
    setupFormValidation();
});

// Close alert messages
function setupAlertClosers() {
    const closeButtons = document.querySelectorAll('.close-alert');
    closeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            this.parentElement.style.display = 'none';
        });
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.display = 'none';
        }, 5000);
    });
}

// Form Validation
function setupFormValidation() {
    const checkoutForm = document.querySelector('.checkout-form');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function(e) {
            if (!validateCheckoutForm()) {
                e.preventDefault();
                alert('Please fill in all required fields correctly.');
            }
        });
    }
}

function validateCheckoutForm() {
    const name = document.getElementById('customer_name');
    const email = document.getElementById('customer_email');
    const address = document.getElementById('shipping_address');
    const city = document.getElementById('shipping_city');
    const payment = document.getElementById('payment_method');

    if (!name || !name.value.trim()) {
        highlightError(name);
        return false;
    }

    if (!email || !isValidEmail(email.value)) {
        highlightError(email);
        return false;
    }

    if (!address || !address.value.trim()) {
        highlightError(address);
        return false;
    }

    if (!city || !city.value.trim()) {
        highlightError(city);
        return false;
    }

    if (!payment || !payment.value) {
        highlightError(payment);
        return false;
    }

    return true;
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function highlightError(element) {
    if (element) {
        element.style.borderColor = '#e74c3c';
        element.style.boxShadow = '0 0 5px rgba(231, 76, 60, 0.3)';
    }
}

// Quantity Selectors
function increaseQty() {
    const input = document.getElementById('quantity');
    if (input) {
        const maxStock = input.getAttribute('max');
        if (parseInt(input.value) < parseInt(maxStock)) {
            input.value = parseInt(input.value) + 1;
        }
    }
}

function decreaseQty() {
    const input = document.getElementById('quantity');
    if (input && parseInt(input.value) > 1) {
        input.value = parseInt(input.value) - 1;
    }
}

// Cart Operations
function updateCart(productId, quantity) {
    if (quantity < 1) {
        removeFromCart(productId);
        return;
    }

    const formData = new FormData();
    formData.append('quantity', quantity);

    fetch(`/update-cart/${productId}`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        }
    })
    .catch(error => console.error('Error:', error));
}

function removeFromCart(productId) {
    if (confirm('Are you sure you want to remove this item?')) {
        window.location.href = `/remove-from-cart/${productId}`;
    }
}

// Sort and Filter
function sortProducts(sortType) {
    const currentUrl = new URL(window.location);
    currentUrl.searchParams.set('sort', sortType);
    window.location.href = currentUrl.toString();
}

function filterByCategory(category) {
    const currentUrl = new URL(window.location);
    if (category) {
        currentUrl.searchParams.set('category', category);
    } else {
        currentUrl.searchParams.delete('category');
    }
    window.location.href = currentUrl.toString();
}

// API calls for Admin
async function updateOrderStatus(orderId, status) {
    try {
        const response = await fetch(`/api/order/${orderId}/status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: status })
        });

        if (response.ok) {
            const data = await response.json();
            alert('Order status updated successfully!');
            location.reload();
        } else {
            alert('Error updating order status');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Get all products (API)
async function fetchProducts() {
    try {
        const response = await fetch('/api/products');
        const products = await response.json();
        return products;
    } catch (error) {
        console.error('Error fetching products:', error);
        return [];
    }
}

// Get all orders (API)
async function fetchOrders() {
    try {
        const response = await fetch('/api/orders');
        const orders = await response.json();
        return orders;
    } catch (error) {
        console.error('Error fetching orders:', error);
        return [];
    }
}

// Product search
function searchProducts(query) {
    const cards = document.querySelectorAll('.product-card');
    const queryLower = query.toLowerCase();

    cards.forEach(card => {
        const name = card.querySelector('h3')?.textContent.toLowerCase() || '';
        const category = card.querySelector('.category')?.textContent.toLowerCase() || '';
        const description = card.querySelector('.description')?.textContent.toLowerCase() || '';

        if (name.includes(queryLower) || category.includes(queryLower) || description.includes(queryLower)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Print order
function printOrder(orderId) {
    const printWindow = window.open(`/order/${orderId}`, '_blank');
    setTimeout(() => {
        printWindow.print();
    }, 250);
}

// Export to CSV (for admin)
function exportOrdersToCSV() {
    fetchOrders().then(orders => {
        let csv = 'Order Number,Customer,Email,Total,Status,Date\n';

        orders.forEach(order => {
            csv += `"${order.order_number}","${order.customer_name}","${order.customer_email}",${order.total_amount},"${order.status}","${order.created_at}"\n`;
        });

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'orders.csv';
        a.click();
        window.URL.revokeObjectURL(url);
    });
}

// Mobile menu toggle (if needed)
function toggleMobileMenu() {
    const navMenu = document.querySelector('.nav-menu');
    if (navMenu) {
        navMenu.classList.toggle('active');
    }
}

// Price filter
function filterByPrice(minPrice, maxPrice) {
    const cards = document.querySelectorAll('.product-card');

    cards.forEach(card => {
        const priceText = card.querySelector('.price')?.textContent || '';
        const price = parseFloat(priceText.replace('$', ''));

        if (price >= minPrice && price <= maxPrice) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// Add to wishlist (localStorage)
function addToWishlist(productId, productName) {
    let wishlist = JSON.parse(localStorage.getItem('wishlist') || '{}');
    wishlist[productId] = productName;
    localStorage.setItem('wishlist', JSON.stringify(wishlist));
    alert(`${productName} added to wishlist!`);
}

// Get wishlist
function getWishlist() {
    return JSON.parse(localStorage.getItem('wishlist') || '{}');
}

// Share product
function shareProduct(productName, productUrl) {
    const url = encodeURIComponent(window.location.href);
    const text = encodeURIComponent(`Check out ${productName} at Anupam SweatsShop!`);

    const shareUrl = `https://twitter.com/intent/tweet?url=${url}&text=${text}`;
    window.open(shareUrl, '_blank');
}

// Smooth scroll
function smoothScroll(target) {
    const element = document.querySelector(target);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}