const express = require('express');
const router = express.Router();
const { createLoan, getLoans, approveLoan, repayLoan, getLoanGuidance } = require('../controllers/loanController');
const auth = require('../middleware/auth');
const roleCheck = require('../middleware/roleCheck');

router.post('/', auth, createLoan);
router.get('/', auth, getLoans);
router.post('/:loan_id/approve', auth, roleCheck(['admin', 'master']), approveLoan);
router.post('/repay', auth, repayLoan);
router.get('/guidance', auth, getLoanGuidance);

module.exports = router;
