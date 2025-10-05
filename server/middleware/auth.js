const jwt = require('jsonwebtoken');
const { promisePool } = require('../config/db');

const auth = async (req, res, next) => {
  try {
    const token = req.header('Authorization')?.replace('Bearer ', '');
    
    if (!token) {
      return res.status(401).json({ success: false, message: 'No authentication token provided' });
    }

    const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key');
    const [users] = await promisePool.query('SELECT * FROM users WHERE id = ?', [decoded.id]);
    
    if (users.length === 0) {
      return res.status(401).json({ success: false, message: 'User not found' });
    }

    req.user = users[0];
    next();
  } catch (error) {
    res.status(401).json({ success: false, message: 'Invalid authentication token' });
  }
};

module.exports = auth;
