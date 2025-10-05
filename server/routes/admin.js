const express = require('express');
const router = express.Router();
const { getAllUsers, updateSettings, getSettings, getDashboardStats } = require('../controllers/adminController');
const auth = require('../middleware/auth');
const roleCheck = require('../middleware/roleCheck');

router.get('/users', auth, roleCheck(['admin', 'master', 'master_assistant']), getAllUsers);
router.post('/settings', auth, roleCheck(['master']), updateSettings);
router.get('/settings', auth, roleCheck(['admin', 'master', 'master_assistant']), getSettings);
router.get('/dashboard', auth, roleCheck(['admin', 'master', 'master_assistant']), getDashboardStats);

module.exports = router;
