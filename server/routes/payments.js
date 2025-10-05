const express = require('express');
const router = express.Router();
const { transferMoney, getPayments, detectSuspiciousActivity } = require('../controllers/paymentController');
const auth = require('../middleware/auth');
const roleCheck = require('../middleware/roleCheck');

router.post('/transfer', auth, transferMoney);
router.get('/', auth, getPayments);
router.get('/fraud-detection', auth, roleCheck(['admin', 'master']), detectSuspiciousActivity);

module.exports = router;
