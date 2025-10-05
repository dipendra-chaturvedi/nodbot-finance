const express = require('express');
const router = express.Router();
const { createInvestment, getInvestments, getInvestmentGuidance } = require('../controllers/investmentController');
const auth = require('../middleware/auth');

router.post('/', auth, createInvestment);
router.get('/', auth, getInvestments);
router.get('/guidance', auth, getInvestmentGuidance);

module.exports = router;
