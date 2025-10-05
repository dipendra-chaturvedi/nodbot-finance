const API_URL = 'http://localhost:5000/api';
let authToken = localStorage.getItem('authToken');
let currentUser = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    if (authToken) {
        loadCurrentUser();
    }
    
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('register-form').addEventListener('submit', handleRegister);
});

// Authentication
async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            authToken = data.token;
            localStorage.setItem('authToken', authToken);
            currentUser = data.user;
            showDashboard();
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Login failed');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    const role = document.getElementById('reg-role').value;
    
    try {
        const response = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password, role })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Registration successful! Please login.');
            showLogin();
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('Registration error:', error);
        alert('Registration failed');
    }
}

async function loadCurrentUser() {
    try {
        const response = await fetch(`${API_URL}/auth/me`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentUser = data.user;
            document.getElementById('login-section').classList.add('hidden');
            document.getElementById('nav-menu').classList.remove('hidden');
            showDashboard();
        } else {
            logout();
        }
    } catch (error) {
        console.error('Load user error:', error);
        logout();
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    document.getElementById('login-section').classList.remove('hidden');
    document.getElementById('nav-menu').classList.add('hidden');
    hideAllSections();
}

// Navigation
function hideAllSections() {
    const sections = ['login-section', 'register-section', 'dashboard-section', 'loans-section', 'investments-section', 'payments-section'];
    sections.forEach(id => document.getElementById(id).classList.add('hidden'));
}

function showLogin() {
    hideAllSections();
    document.getElementById('login-section').classList.remove('hidden');
}

function showRegister() {
    hideAllSections();
    document.getElementById('register-section').classList.remove('hidden');
}

async function showDashboard() {
    hideAllSections();
    document.getElementById('dashboard-section').classList.remove('hidden');
    
    // Update balance
    document.getElementById('user-balance').textContent = `₹${currentUser.balance}`;
    
    // Load stats
    try {
        const [loansRes, investmentsRes, paymentsRes] = await Promise.all([
            fetch(`${API_URL}/loans`, { headers: { 'Authorization': `Bearer ${authToken}` }}),
            fetch(`${API_URL}/investments`, { headers: { 'Authorization': `Bearer ${authToken}` }}),
            fetch(`${API_URL}/payments`, { headers: { 'Authorization': `Bearer ${authToken}` }})
        ]);
        
        const loans = await loansRes.json();
        const investments = await investmentsRes.json();
        const payments = await paymentsRes.json();
        
        document.getElementById('active-loans').textContent = loans.loans?.length || 0;
        document.getElementById('active-investments').textContent = investments.investments?.length || 0;
        document.getElementById('total-transactions').textContent = payments.payments?.length || 0;
        
        // Create chart
        createDashboardChart(loans.loans || [], investments.investments || []);
    } catch (error) {
        console.error('Load dashboard error:', error);
    }
}

function createDashboardChart(loans, investments) {
    const ctx = document.getElementById('dashboard-chart').getContext('2d');
    
    const totalLoans = loans.reduce((sum, l) => sum + parseFloat(l.amount), 0);
    const totalInvestments = investments.reduce((sum, i) => sum + parseFloat(i.amount), 0);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Loans', 'Investments', 'Balance'],
            datasets: [{
                label: 'Amount (₹)',
                data: [totalLoans, totalInvestments, currentUser.balance],
                backgroundColor: ['#667eea', '#764ba2', '#f093fb']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                title: { display: true, text: 'Financial Overview' }
            }
        }
    });
}

async function showLoans() {
    hideAllSections();
    document.getElementById('loans-section').classList.remove('hidden');
    
    try {
        const response = await fetch(`${API_URL}/loans`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        const data = await response.json();
        
        const loansList = document.getElementById('loans-list');
        loansList.innerHTML = '';
        
        if (data.loans && data.loans.length > 0) {
            data.loans.forEach(loan => {
                const loanCard = `
                    <div class="border p-4 mb-4 rounded">
                        <h3 class="font-bold">${loan.loan_type.toUpperCase()} - ₹${loan.amount}</h3>
                        <p>Status: <span class="font-semibold">${loan.status}</span></p>
                        <p>Interest Rate: ${loan.interest_rate}%</p>
                        <p>Monthly Payment: ₹${loan.monthly_payment}</p>
                        <p>Total Repayment: ₹${loan.total_repayment}</p>
                        <p>Amount Paid: ₹${loan.amount_paid}</p>
                        ${loan.status === 'approved' && currentUser.role === 'user' ? 
                            `<button onclick="repayLoan(${loan.id})" class="btn-primary mt-2">Repay</button>` : ''}
                        ${loan.status === 'pending' && ['admin', 'master'].includes(currentUser.role) ? 
                            `<button onclick="approveLoan(${loan.id})" class="btn-primary mt-2">Approve</button>` : ''}
                    </div>
                `;
                loansList.innerHTML += loanCard;
            });
        } else {
            loansList.innerHTML = '<p class="text-gray-600">No loans found</p>';
        }
    } catch (error) {
        console.error('Load loans error:', error);
    }
}

async function showInvestments() {
    hideAllSections();
    document.getElementById('investments-section').classList.remove('hidden');
    
    try {
        const response = await fetch(`${API_URL}/investments`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        const data = await response.json();
        
        const investmentsList = document.getElementById('investments-list');
        investmentsList.innerHTML = '';
        
        if (data.investments && data.investments.length > 0) {
            data.investments.forEach(inv => {
                const invCard = `
                    <div class="border p-4 mb-4 rounded">
                        <h3 class="font-bold">${inv.investment_type.toUpperCase()} - ₹${inv.amount}</h3>
                        <p>Frequency: ${inv.frequency}</p>
                        <p>Expected Return: ${inv.expected_return}%</p>
                        <p>Maturity Amount: ₹${inv.maturity_amount}</p>
                        <p>Maturity Date: ${new Date(inv.maturity_date).toLocaleDateString()}</p>
                        <p>Status: <span class="font-semibold">${inv.status}</span></p>
                    </div>
                `;
                investmentsList.innerHTML += invCard;
            });
        } else {
            investmentsList.innerHTML = '<p class="text-gray-600">No investments found</p>';
        }
    } catch (error) {
        console.error('Load investments error:', error);
    }
}

async function showPayments() {
    hideAllSections();
    document.getElementById('payments-section').classList.remove('hidden');
    
    try {
        const response = await fetch(`${API_URL}/payments`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        const data = await response.json();
        
        const paymentsList = document.getElementById('payments-list');
        paymentsList.innerHTML = '';
        
        if (data.payments && data.payments.length > 0) {
            data.payments.forEach(payment => {
                const paymentCard = `
                    <div class="border p-4 mb-4 rounded">
                        <p><strong>From:</strong> ${payment.sender_name}</p>
                        <p><strong>To:</strong> ${payment.receiver_name}</p>
                        <p><strong>Amount:</strong> ₹${payment.amount}</p>
                        <p><strong>Reason:</strong> ${payment.reason || 'N/A'}</p>
                        <p><strong>Type:</strong> ${payment.transaction_type}</p>
                        <p><strong>Date:</strong> ${new Date(payment.created_at).toLocaleString()}</p>
                    </div>
                `;
                paymentsList.innerHTML += paymentCard;
            });
        } else {
            paymentsList.innerHTML = '<p class="text-gray-600">No payments found</p>';
        }
    } catch (error) {
        console.error('Load payments error:', error);
    }
}

// Loan functions
function showCreateLoan() {
    const loanType = prompt('Enter loan type (personal/business/sip/swp):');
    const amount = prompt('Enter loan amount:');
    const termMonths = prompt('Enter loan term (months):');
    
    if (loanType && amount && termMonths) {
        createLoan(loanType, amount, termMonths);
    }
}

async function createLoan(loanType, amount, termMonths) {
    try {
        const response = await fetch(`${API_URL}/loans`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ loan_type: loanType, amount, term_months: termMonths })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Loan request created successfully!');
            showLoans();
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('Create loan error:', error);
        alert('Failed to create loan request');
    }
}

async function approveLoan(loanId) {
    if (!confirm('Are you sure you want to approve this loan?')) return;
    
    try {
        const response = await fetch(`${API_URL}/loans/${loanId}/approve`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Loan approved successfully!');
            showLoans();
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('Approve loan error:', error);
        alert('Failed to approve loan');
    }
}

async function repayLoan(loanId) {
    const amount = prompt('Enter repayment amount:');
    
    if (!amount) return;
    
    try {
        const response = await fetch(`${API_URL}/loans/repay`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ loan_id: loanId, amount: parseFloat(amount) })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(`Repayment successful! Remaining: ₹${data.remaining}`);
            loadCurrentUser();
            showLoans();
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('Repay loan error:', error);
        alert('Failed to process repayment');
    }
}

// Investment functions
function showCreateInvestment() {
    const investmentType = prompt('Enter investment type (sip/swp/lumpsum):');
    const amount = prompt('Enter investment amount:');
    const frequency = prompt('Enter frequency (daily/weekly/monthly):');
    const durationMonths = prompt('Enter duration (months):');
    const expectedReturn = prompt('Enter expected return rate (%):');
    
    if (investmentType && amount && frequency && durationMonths && expectedReturn) {
        createInvestment(investmentType, amount, frequency, durationMonths, expectedReturn);
    }
}

async function createInvestment(investmentType, amount, frequency, durationMonths, expectedReturn) {
    try {
        const response = await fetch(`${API_URL}/investments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                investment_type: investmentType,
                amount,
                frequency,
                duration_months: durationMonths,
                expected_return: expectedReturn
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Investment created successfully!');
            loadCurrentUser();
            showInvestments();
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('Create investment error:', error);
        alert('Failed to create investment');
    }
}

// Payment functions
function showTransferMoney() {
    const receiverId = prompt('Enter receiver user ID:');
    const amount = prompt('Enter amount:');
    const reason = prompt('Enter reason:');
    
    if (receiverId && amount) {
        transferMoney(receiverId, amount, reason);
    }
}

async function transferMoney(receiverId, amount, reason) {
    try {
        const response = await fetch(`${API_URL}/payments/transfer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ receiver_id: receiverId, amount, reason })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Transfer successful!');
            loadCurrentUser();
            showPayments();
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('Transfer error:', error);
        alert('Failed to transfer money');
    }
}
