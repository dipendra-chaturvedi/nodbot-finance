const { promisePool } = require('../config/db');

// Transfer money
exports.transferMoney = async (req, res) => {
  try {
    const { receiver_id, amount, reason } = req.body;
    const sender_id = req.user.id;

    if (sender_id === receiver_id) {
      return res.status(400).json({ success: false, message: 'Cannot transfer to yourself' });
    }

    // Check sender balance
    if (req.user.balance < amount) {
      return res.status(400).json({ success: false, message: 'Insufficient balance' });
    }

    // Check receiver exists
    const [receivers] = await promisePool.query('SELECT * FROM users WHERE id = ?', [receiver_id]);
    if (receivers.length === 0) {
      return res.status(404).json({ success: false, message: 'Receiver not found' });
    }

    // Perform transfer
    await promisePool.query('UPDATE users SET balance = balance - ? WHERE id = ?', [amount, sender_id]);
    await promisePool.query('UPDATE users SET balance = balance + ? WHERE id = ?', [amount, receiver_id]);

    // Record payment
    const [result] = await promisePool.query(
      'INSERT INTO payments (sender_id, receiver_id, amount, reason, transaction_type) VALUES (?, ?, ?, ?, ?)',
      [sender_id, receiver_id, amount, reason, 'transfer']
    );

    res.json({
      success: true,
      message: 'Transfer successful',
      payment: {
        id: result.insertId,
        amount,
        receiver: receivers[0].username
      }
    });
  } catch (error) {
    console.error('Transfer error:', error);
    res.status(500).json({ success: false, message: 'Error processing transfer' });
  }
};

// Get payment history
exports.getPayments = async (req, res) => {
  try {
    let query = `
      SELECT p.*, 
             s.username as sender_name, 
             r.username as receiver_name 
      FROM payments p
      JOIN users s ON p.sender_id = s.id
      JOIN users r ON p.receiver_id = r.id
    `;
    const params = [];

    if (req.user.role === 'user') {
      query += ' WHERE p.sender_id = ? OR p.receiver_id = ?';
      params.push(req.user.id, req.user.id);
    }

    query += ' ORDER BY p.created_at DESC';

    const [payments] = await promisePool.query(query, params);

    res.json({ success: true, payments });
  } catch (error) {
    console.error('Get payments error:', error);
    res.status(500).json({ success: false, message: 'Error fetching payments' });
  }
};

// AI Fraud detection
exports.detectSuspiciousActivity = async (req, res) => {
  try {
    const user_id = req.user.id;

    // Get recent transactions
    const [payments] = await promisePool.query(
      `SELECT * FROM payments WHERE sender_id = ? AND created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)`,
      [user_id]
    );

    const total_sent_24h = payments.reduce((sum, p) => sum + parseFloat(p.amount), 0);
    const transaction_count = payments.length;

    // Suspicious activity indicators
    const alerts = [];

    if (transaction_count > 10) {
      alerts.push('High transaction frequency detected (>10 in 24 hours)');
    }

    if (total_sent_24h > req.user.balance * 2) {
      alerts.push('Transaction volume exceeds typical patterns');
    }

    const large_transactions = payments.filter(p => parseFloat(p.amount) > 10000);
    if (large_transactions.length > 0) {
      alerts.push(`${large_transactions.length} large transaction(s) detected (>10,000)`);
    }

    res.json({
      success: true,
      analysis: {
        transaction_count,
        total_amount_24h: total_sent_24h.toFixed(2),
        suspicious: alerts.length > 0,
        alerts,
        risk_score: Math.min(100, alerts.length * 30)
      }
    });
  } catch (error) {
    console.error('Fraud detection error:', error);
    res.status(500).json({ success: false, message: 'Error analyzing transactions' });
  }
};
