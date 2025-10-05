const { promisePool } = require('../config/db');

// Create investment
exports.createInvestment = async (req, res) => {
  try {
    const { investment_type, amount, frequency, duration_months, expected_return } = req.body;
    const user_id = req.user.id;

    // Check balance
    if (req.user.balance < amount) {
      return res.status(400).json({ success: false, message: 'Insufficient balance' });
    }

    // Calculate maturity
    const maturity_amount = amount * (1 + (expected_return / 100) * (duration_months / 12));
    const maturity_date = new Date();
    maturity_date.setMonth(maturity_date.getMonth() + duration_months);

    // Insert investment
    const [result] = await promisePool.query(
      `INSERT INTO investments (user_id, investment_type, amount, frequency, duration_months, expected_return, maturity_amount, maturity_date)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [user_id, investment_type, amount, frequency, duration_months, expected_return, maturity_amount, maturity_date]
    );

    // Deduct from balance
    await promisePool.query('UPDATE users SET balance = balance - ? WHERE id = ?', [amount, user_id]);

    // Record payment
    await promisePool.query(
      'INSERT INTO payments (sender_id, receiver_id, amount, reason, transaction_type) VALUES (?, ?, ?, ?, ?)',
      [user_id, user_id, amount, `Investment: ${investment_type}`, 'investment']
    );

    res.status(201).json({
      success: true,
      message: 'Investment created successfully',
      investment: {
        id: result.insertId,
        investment_type,
        amount,
        maturity_amount: maturity_amount.toFixed(2),
        maturity_date
      }
    });
  } catch (error) {
    console.error('Create investment error:', error);
    res.status(500).json({ success: false, message: 'Error creating investment' });
  }
};

// Get investments
exports.getInvestments = async (req, res) => {
  try {
    let query = 'SELECT i.*, u.username FROM investments i JOIN users u ON i.user_id = u.id';
    const params = [];

    if (req.user.role === 'user') {
      query += ' WHERE i.user_id = ?';
      params.push(req.user.id);
    }

    const [investments] = await promisePool.query(query, params);

    res.json({ success: true, investments });
  } catch (error) {
    console.error('Get investments error:', error);
    res.status(500).json({ success: false, message: 'Error fetching investments' });
  }
};

// AI Investment guidance
exports.getInvestmentGuidance = async (req, res) => {
  try {
    const { amount, duration_months, investment_type } = req.query;
    const user = req.user;

    // Calculate potential returns based on investment type
    const return_rates = {
      sip: 12, // 12% annual return
      swp: 8,  // 8% annual return
      lumpsum: 10 // 10% annual return
    };

    const annual_return = return_rates[investment_type] || 10;
    const maturity_amount = amount * (1 + (annual_return / 100) * (duration_months / 12));
    const total_profit = maturity_amount - amount;

    // Risk assessment
    const investment_ratio = (amount / user.balance) * 100;
    const risk_level = investment_ratio > 80 ? 'high' : investment_ratio > 50 ? 'medium' : 'low';

    res.json({
      success: true,
      guidance: {
        investment_type,
        amount,
        duration_months,
        expected_annual_return: annual_return + '%',
        maturity_amount: maturity_amount.toFixed(2),
        total_profit: total_profit.toFixed(2),
        monthly_profit: (total_profit / duration_months).toFixed(2),
        investment_ratio: investment_ratio.toFixed(2) + '%',
        risk_level,
        recommendation: risk_level === 'low'
          ? 'Excellent investment opportunity within your financial capacity.'
          : risk_level === 'medium'
          ? 'Good investment but consider maintaining emergency funds.'
          : 'High investment ratio. Ensure you have sufficient liquid funds.'
      }
    });
  } catch (error) {
    console.error('Investment guidance error:', error);
    res.status(500).json({ success: false, message: 'Error generating investment guidance' });
  }
};
