const { promisePool } = require('../config/db');

// Create loan request
exports.createLoan = async (req, res) => {
  try {
    const { loan_type, amount, term_months } = req.body;
    const user_id = req.user.id;

    // Get interest rate from admin settings
    const [settings] = await promisePool.query(
      'SELECT setting_value FROM admin_settings WHERE setting_key = ?',
      [`${loan_type}_interest_rate`]
    );

    const interest_rate = settings.length > 0 ? parseFloat(settings[0].setting_value) : 10.0;

    // Calculate monthly payment and total repayment
    const monthlyInterestRate = interest_rate / 100 / 12;
    const monthly_payment = (amount * monthlyInterestRate * Math.pow(1 + monthlyInterestRate, term_months)) / 
                           (Math.pow(1 + monthlyInterestRate, term_months) - 1);
    const total_repayment = monthly_payment * term_months;

    // Insert loan
    const [result] = await promisePool.query(
      `INSERT INTO loans (user_id, loan_type, amount, interest_rate, term_months, monthly_payment, total_repayment) 
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [user_id, loan_type, amount, interest_rate, term_months, monthly_payment, total_repayment]
    );

    res.status(201).json({
      success: true,
      message: 'Loan request created successfully',
      loan: {
        id: result.insertId,
        loan_type,
        amount,
        interest_rate,
        term_months,
        monthly_payment: monthly_payment.toFixed(2),
        total_repayment: total_repayment.toFixed(2),
        status: 'pending'
      }
    });
  } catch (error) {
    console.error('Create loan error:', error);
    res.status(500).json({ success: false, message: 'Error creating loan request' });
  }
};

// Get loans (role-based)
exports.getLoans = async (req, res) => {
  try {
    let query = 'SELECT l.*, u.username, u.email FROM loans l JOIN users u ON l.user_id = u.id';
    const params = [];

    if (req.user.role === 'user') {
      query += ' WHERE l.user_id = ?';
      params.push(req.user.id);
    }

    const [loans] = await promisePool.query(query, params);

    res.json({ success: true, loans });
  } catch (error) {
    console.error('Get loans error:', error);
    res.status(500).json({ success: false, message: 'Error fetching loans' });
  }
};

// Approve loan (admin/master only)
exports.approveLoan = async (req, res) => {
  try {
    const { loan_id } = req.params;
    const approved_by = req.user.id;

    // Get loan details
    const [loans] = await promisePool.query('SELECT * FROM loans WHERE id = ?', [loan_id]);

    if (loans.length === 0) {
      return res.status(404).json({ success: false, message: 'Loan not found' });
    }

    const loan = loans[0];

    // Update loan status
    await promisePool.query(
      'UPDATE loans SET status = ?, approved_by = ? WHERE id = ?',
      ['approved', approved_by, loan_id]
    );

    // Add amount to user balance
    await promisePool.query(
      'UPDATE users SET balance = balance + ? WHERE id = ?',
      [loan.amount, loan.user_id]
    );

    // Record payment
    await promisePool.query(
      'INSERT INTO payments (sender_id, receiver_id, amount, reason, transaction_type) VALUES (?, ?, ?, ?, ?)',
      [approved_by, loan.user_id, loan.amount, `Loan approved: ${loan.loan_type}`, 'transfer']
    );

    res.json({ success: true, message: 'Loan approved successfully' });
  } catch (error) {
    console.error('Approve loan error:', error);
    res.status(500).json({ success: false, message: 'Error approving loan' });
  }
};

// Repay loan
exports.repayLoan = async (req, res) => {
  try {
    const { loan_id, amount } = req.body;
    const user_id = req.user.id;

    // Get loan and user
    const [loans] = await promisePool.query('SELECT * FROM loans WHERE id = ? AND user_id = ?', [loan_id, user_id]);

    if (loans.length === 0) {
      return res.status(404).json({ success: false, message: 'Loan not found' });
    }

    const loan = loans[0];

    if (req.user.balance < amount) {
      return res.status(400).json({ success: false, message: 'Insufficient balance' });
    }

    // Update loan amount paid
    const new_amount_paid = parseFloat(loan.amount_paid) + parseFloat(amount);
    const new_status = new_amount_paid >= loan.total_repayment ? 'paid' : loan.status;

    await promisePool.query(
      'UPDATE loans SET amount_paid = ?, status = ? WHERE id = ?',
      [new_amount_paid, new_status, loan_id]
    );

    // Deduct from user balance
    await promisePool.query('UPDATE users SET balance = balance - ? WHERE id = ?', [amount, user_id]);

    // Record payment
    await promisePool.query(
      'INSERT INTO payments (sender_id, receiver_id, amount, reason, transaction_type) VALUES (?, ?, ?, ?, ?)',
      [user_id, loan.approved_by, amount, `Loan repayment for loan #${loan_id}`, 'loan_repayment']
    );

    res.json({ 
      success: true, 
      message: 'Loan repayment successful',
      remaining: (loan.total_repayment - new_amount_paid).toFixed(2)
    });
  } catch (error) {
    console.error('Repay loan error:', error);
    res.status(500).json({ success: false, message: 'Error processing loan repayment' });
  }
};

// AI Guidance for loan
exports.getLoanGuidance = async (req, res) => {
  try {
    const { amount, term_months, loan_type } = req.query;
    const user = req.user;

    // Get settings
    const [settings] = await promisePool.query(
      'SELECT setting_value FROM admin_settings WHERE setting_key = ?',
      [`${loan_type}_interest_rate`]
    );

    const interest_rate = settings.length > 0 ? parseFloat(settings[0].setting_value) : 10.0;

    // Calculate repayment capacity
    const monthlyInterestRate = interest_rate / 100 / 12;
    const monthly_payment = (amount * monthlyInterestRate * Math.pow(1 + monthlyInterestRate, term_months)) / 
                           (Math.pow(1 + monthlyInterestRate, term_months) - 1);
    const total_repayment = monthly_payment * term_months;
    const total_interest = total_repayment - amount;

    // AI recommendations
    const max_safe_loan = user.balance * 5; // 5x current balance
    const risk_level = amount > max_safe_loan ? 'high' : amount > max_safe_loan * 0.7 ? 'medium' : 'low';

    res.json({
      success: true,
      guidance: {
        requested_amount: amount,
        monthly_payment: monthly_payment.toFixed(2),
        total_repayment: total_repayment.toFixed(2),
        total_interest: total_interest.toFixed(2),
        interest_rate: interest_rate,
        recommended_max_loan: max_safe_loan.toFixed(2),
        risk_level,
        recommendation: risk_level === 'low' 
          ? 'This loan is within safe limits for your financial profile.'
          : risk_level === 'medium'
          ? 'Consider reducing the loan amount or extending the term.'
          : 'This loan exceeds recommended limits. High risk of default.'
      }
    });
  } catch (error) {
    console.error('Loan guidance error:', error);
    res.status(500).json({ success: false, message: 'Error generating loan guidance' });
  }
};
