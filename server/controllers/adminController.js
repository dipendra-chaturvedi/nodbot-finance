const { promisePool } = require('../config/db');

// Get all users
exports.getAllUsers = async (req, res) => {
  try {
    const [users] = await promisePool.query('SELECT id, username, email, role, balance, created_at FROM users');
    res.json({ success: true, users });
  } catch (error) {
    console.error('Get users error:', error);
    res.status(500).json({ success: false, message: 'Error fetching users' });
  }
};

// Update admin settings
exports.updateSettings = async (req, res) => {
  try {
    const { setting_key, setting_value, description } = req.body;
    const updated_by = req.user.id;

    await promisePool.query(
      `INSERT INTO admin_settings (setting_key, setting_value, description, updated_by)
       VALUES (?, ?, ?, ?)
       ON DUPLICATE KEY UPDATE setting_value = ?, description = ?, updated_by = ?`,
      [setting_key, setting_value, description, updated_by, setting_value, description, updated_by]
    );

    res.json({ success: true, message: 'Settings updated successfully' });
  } catch (error) {
    console.error('Update settings error:', error);
    res.status(500).json({ success: false, message: 'Error updating settings' });
  }
};

// Get admin settings
exports.getSettings = async (req, res) => {
  try {
    const [settings] = await promisePool.query('SELECT * FROM admin_settings');
    res.json({ success: true, settings });
  } catch (error) {
    console.error('Get settings error:', error);
    res.status(500).json({ success: false, message: 'Error fetching settings' });
  }
};

// Dashboard stats
exports.getDashboardStats = async (req, res) => {
  try {
    const [[userCount]] = await promisePool.query('SELECT COUNT(*) as count FROM users');
    const [[loanStats]] = await promisePool.query(
      'SELECT COUNT(*) as count, SUM(amount) as total_amount FROM loans WHERE status = "approved"'
    );
    const [[investmentStats]] = await promisePool.query(
      'SELECT COUNT(*) as count, SUM(amount) as total_amount FROM investments WHERE status = "active"'
    );
    const [[paymentStats]] = await promisePool.query(
      'SELECT COUNT(*) as count, SUM(amount) as total_amount FROM payments WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)'
    );

    res.json({
      success: true,
      stats: {
        total_users: userCount.count,
        active_loans: loanStats.count,
        total_loan_amount: loanStats.total_amount || 0,
        active_investments: investmentStats.count,
        total_investment_amount: investmentStats.total_amount || 0,
        monthly_transactions: paymentStats.count,
        monthly_transaction_volume: paymentStats.total_amount || 0
      }
    });
  } catch (error) {
    console.error('Dashboard stats error:', error);
    res.status(500).json({ success: false, message: 'Error fetching dashboard stats' });
  }
};
