import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Alert,
  MenuItem
} from '@mui/material';
import { predictChurn } from './api';

function GetPrediction() {
  const [errors, setErrors] = useState({});
  const initialFormData = {
  AMOUNT_RUB_CLO_PRC: '',
  SUM_TRAN_AUT_TENDENCY3M: '',
  CNT_TRAN_AUT_TENDENCY3M: '',
  REST_AVG_CUR: '',
  CR_PROD_CNT_TOVR: '',
  TRANS_COUNT_ATM_PRC: '',
  AMOUNT_RUB_ATM_PRC: '',
  AGE: '',
  CNT_TRAN_MED_TENDENCY3M: '',
  SUM_TRAN_MED_TENDENCY3M: '',
  SUM_TRAN_CLO_TENDENCY3M: '',
  CNT_TRAN_CLO_TENDENCY3M: '',
  CNT_TRAN_SUP_TENDENCY3M: '',
  TURNOVER_DYNAMIC_CUR_1M: '',
  REST_DYNAMIC_PAYM_3M: '',
  SUM_TRAN_SUP_TENDENCY3M: '',
  SUM_TRAN_ATM_TENDENCY3M: '',
  SUM_TRAN_SUP_TENDENCY1M: '',
  SUM_TRAN_ATM_TENDENCY1M: '',
  CNT_TRAN_SUP_TENDENCY1M: '',
  TURNOVER_DYNAMIC_CUR_3M: '',
  CLNT_SETUP_TENOR: '',
  TURNOVER_DYNAMIC_PAYM_3M: '',
  TURNOVER_DYNAMIC_PAYM_1M: '',
  TRANS_AMOUNT_TENDENCY3M: '',
  TRANS_CNT_TENDENCY3M: '',
  PACK: '',
  };

const [formData, setFormData] = useState(initialFormData);

  const [prediction, setPrediction] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleReset = () => {
    setFormData(initialFormData);
    setErrors({});
    setPrediction(null);
    setError('');
};

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const validate = () => {
    const newErrors = {};
    const floatRegex = /^-?\d+(\.\d{1,2})?$/;

    const checkFloat = (key, label) => {
      const v = formData[key];
      if (v === '') {
        newErrors[key] = `${label} is required`;
      } else if (!floatRegex.test(v)) {
        newErrors[key] = `${label} must be a number with up to 2 decimals`;
      }
    };

    checkFloat('AMOUNT_RUB_CLO_PRC', 'AMOUNT_RUB_CLO_PRC');
    checkFloat('SUM_TRAN_AUT_TENDENCY3M', 'SUM_TRAN_AUT_TENDENCY3M');
    checkFloat('CNT_TRAN_AUT_TENDENCY3M', 'CNT_TRAN_AUT_TENDENCY3M');
    checkFloat('REST_AVG_CUR', 'REST_AVG_CUR');
    checkFloat('CR_PROD_CNT_TOVR', 'CR_PROD_CNT_TOVR');
    checkFloat('TRANS_COUNT_ATM_PRC', 'TRANS_COUNT_ATM_PRC');
    checkFloat('AMOUNT_RUB_ATM_PRC', 'AMOUNT_RUB_ATM_PRC');
    checkFloat('CNT_TRAN_MED_TENDENCY3M', 'CNT_TRAN_MED_TENDENCY3M');
    checkFloat('SUM_TRAN_MED_TENDENCY3M', 'SUM_TRAN_MED_TENDENCY3M');
    checkFloat('SUM_TRAN_CLO_TENDENCY3M', 'SUM_TRAN_CLO_TENDENCY3M');
    checkFloat('CNT_TRAN_CLO_TENDENCY3M', 'CNT_TRAN_CLO_TENDENCY3M');
    checkFloat('CNT_TRAN_SUP_TENDENCY3M', 'CNT_TRAN_SUP_TENDENCY3M');
    checkFloat('TURNOVER_DYNAMIC_CUR_1M', 'TURNOVER_DYNAMIC_CUR_1M');
    checkFloat('REST_DYNAMIC_PAYM_3M', 'REST_DYNAMIC_PAYM_3M');
    checkFloat('SUM_TRAN_SUP_TENDENCY3M', 'SUM_TRAN_SUP_TENDENCY3M');
    checkFloat('SUM_TRAN_ATM_TENDENCY3M', 'SUM_TRAN_ATM_TENDENCY3M');
    checkFloat('SUM_TRAN_SUP_TENDENCY1M', 'SUM_TRAN_SUP_TENDENCY1M');
    checkFloat('SUM_TRAN_ATM_TENDENCY1M', 'SUM_TRAN_ATM_TENDENCY1M');
    checkFloat('CNT_TRAN_SUP_TENDENCY1M', 'CNT_TRAN_SUP_TENDENCY1M');
    checkFloat('TURNOVER_DYNAMIC_CUR_3M', 'TURNOVER_DYNAMIC_CUR_3M');
    checkFloat('CLNT_SETUP_TENOR', 'CLNT_SETUP_TENOR');
    checkFloat('TURNOVER_DYNAMIC_PAYM_3M', 'TURNOVER_DYNAMIC_PAYM_3M');
    checkFloat('TURNOVER_DYNAMIC_PAYM_1M', 'TURNOVER_DYNAMIC_PAYM_1M');
    checkFloat('TRANS_AMOUNT_TENDENCY3M', 'TRANS_AMOUNT_TENDENCY3M');
    checkFloat('TRANS_CNT_TENDENCY3M', 'TRANS_CNT_TENDENCY3M');

    if (formData.AGE === '') {
    newErrors.AGE = 'AGE is required';
    } else if (!/^\d+$/.test(formData.AGE)) {
    newErrors.AGE = 'AGE must be a whole number';
    } else {
    const ageNum = Number(formData.AGE);
    if (ageNum < 12 || ageNum > 120) {
        newErrors.AGE = 'AGE must be between 12 and 100';
    }
    }

    if (formData.PACK === '') {
      newErrors.PACK = 'PACK is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

const handleSubmit = async (e) => {
  e.preventDefault();
  setError('');
  setPrediction(null);

  // 1) validate first
  if (!validate()) {
    setError('Please fix the highlighted fields.');
    return;
  }

  // 2) build numeric payload
  const numericPayload = Object.fromEntries(
    Object.entries(formData).map(([k, v]) => [k, v === '' ? null : Number(v)])
  );

  setLoading(true);
  try {
    const result = await predictChurn(numericPayload);
    setPrediction(result);
  } catch (err) {
    setError(err.message || 'Prediction failed');
  } finally {
    setLoading(false);
  }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} noValidate>
      <Typography variant="h6" gutterBottom>
        Predict Churn for a Customer
      </Typography>

      <TextField
        label="AMOUNT_RUB_CLO_PRC"
        helperText={errors.AMOUNT_RUB_CLO_PRC || 'Share of clothing‑type transactions in total amount (rub).'}
        name="AMOUNT_RUB_CLO_PRC"
        value={formData.AMOUNT_RUB_CLO_PRC}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.AMOUNT_RUB_CLO_PRC}
      />
      <TextField
        label="SUM_TRAN_AUT_TENDENCY3M"
        helperText={errors.SUM_TRAN_AUT_TENDENCY3M || 'Trend of transaction amount at auto‑related MCC (1–3 months).'}
        name="SUM_TRAN_AUT_TENDENCY3M"
        value={formData.SUM_TRAN_AUT_TENDENCY3M}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.SUM_TRAN_AUT_TENDENCY3M}
      />
      <TextField
        label="CNT_TRAN_AUT_TENDENCY3M"
        helperText={errors.CNT_TRAN_AUT_TENDENCY3M || 'Trend of number of auto‑related transactions (1–3 months).'}
        name="CNT_TRAN_AUT_TENDENCY3M"
        value={formData.CNT_TRAN_AUT_TENDENCY3M}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.CNT_TRAN_AUT_TENDENCY3M}
      />

      <TextField
        label="REST_AVG_CUR"
        helperText={errors.REST_AVG_CUR || 'Average current account balance.'}
        name="REST_AVG_CUR"
        value={formData.REST_AVG_CUR}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.REST_AVG_CUR}
      />
      <TextField
        label="CR_PROD_CNT_TOVR"
        helperText={errors.CR_PROD_CNT_TOVR || 'Number of products used in the period.'}
        name="CR_PROD_CNT_TOVR"
        value={formData.CR_PROD_CNT_TOVR}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.CR_PROD_CNT_TOVR}
      />

      <TextField
        label="TRANS_COUNT_ATM_PRC"
        helperText={errors.TRANS_COUNT_ATM_PRC || 'Share of ATM transactions in total transaction count.'}
        name="TRANS_COUNT_ATM_PRC"
        value={formData.TRANS_COUNT_ATM_PRC}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.TRANS_COUNT_ATM_PRC}
      />
      <TextField
        label="AMOUNT_RUB_ATM_PRC"
        helperText={errors.AMOUNT_RUB_ATM_PRC || 'Share of ATM transactions in total transaction amount (rub).'}
        name="AMOUNT_RUB_ATM_PRC"
        value={formData.AMOUNT_RUB_ATM_PRC}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.AMOUNT_RUB_ATM_PRC}
      />

      <TextField
        label="AGE (years)"
        helperText={errors.AGE || 'Customer age.'}
        name="AGE"
        value={formData.AGE}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.AGE}
      />
      <TextField
        label="CNT_TRAN_MED_TENDENCY3M"
        helperText={errors.CNT_TRAN_MED_TENDENCY3M || 'Trend of number of medical‑related transactions (1–3 months).'}
        name="CNT_TRAN_MED_TENDENCY3M"
        value={formData.CNT_TRAN_MED_TENDENCY3M}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.CNT_TRAN_MED_TENDENCY3M}
      />
      <TextField
        label="SUM_TRAN_MED_TENDENCY3M"
        helperText={errors.SUM_TRAN_MED_TENDENCY3M || 'Trend of medical‑related transaction amounts (1–3 months).'}
        name="SUM_TRAN_MED_TENDENCY3M"
        value={formData.SUM_TRAN_MED_TENDENCY3M}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.SUM_TRAN_MED_TENDENCY3M}
      />

      <TextField
        label="SUM_TRAN_CLO_TENDENCY3M"
        helperText={errors.SUM_TRAN_CLO_TENDENCY3M || 'Trend of clothing‑related transaction amounts (1–3 months).'}
        name="SUM_TRAN_CLO_TENDENCY3M"
        value={formData.SUM_TRAN_CLO_TENDENCY3M}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.SUM_TRAN_CLO_TENDENCY3M}
      />
      <TextField
        label="CNT_TRAN_CLO_TENDENCY3M"
        helperText={errors.CNT_TRAN_CLO_TENDENCY3M || 'Trend of number of clothing‑related transactions (1–3 months).'}
        name="CNT_TRAN_CLO_TENDENCY3M"
        value={formData.CNT_TRAN_CLO_TENDENCY3M}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.CNT_TRAN_CLO_TENDENCY3M}
      />
      <TextField
        label="CNT_TRAN_SUP_TENDENCY3M"
        helperText={errors.CNT_TRAN_SUP_TENDENCY3M || 'Trend of number of supermarket transactions (1–3 months).'}
        name="CNT_TRAN_SUP_TENDENCY3M"
        value={formData.CNT_TRAN_SUP_TENDENCY3M}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.CNT_TRAN_SUP_TENDENCY3M}
      />

      <TextField
        label="TURNOVER_DYNAMIC_CUR_1M"
        helperText={errors.TURNOVER_DYNAMIC_CUR_1M || 'Short‑term trend of monthly turnovers on current accounts (1 month).'}
        name="TURNOVER_DYNAMIC_CUR_1M"
        value={formData.TURNOVER_DYNAMIC_CUR_1M}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.TURNOVER_DYNAMIC_CUR_1M}
      />
      <TextField
        label="REST_DYNAMIC_PAYM_3M"
        helperText={errors.REST_DYNAMIC_PAYM_3M || 'Trend of average balances on payment products (3 months).'}
        name="REST_DYNAMIC_PAYM_3M"
        value={formData.REST_DYNAMIC_PAYM_3M}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.REST_DYNAMIC_PAYM_3M}
      />

      <TextField
        label="SUM_TRAN_SUP_TENDENCY3M"
        helperText={errors.SUM_TRAN_SUP_TENDENCY3M || 'Trend of supermarket transaction amounts (1–3 months).'}
        name="SUM_TRAN_SUP_TENDENCY3M"
        value={formData.SUM_TRAN_SUP_TENDENCY3M}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.SUM_TRAN_SUP_TENDENCY3M}
      />
      <TextField
        label="SUM_TRAN_ATM_TENDENCY3M"
        helperText={errors.SUM_TRAN_ATM_TENDENCY3M || 'Trend of ATM transaction amounts (1–3 months).'}
        name="SUM_TRAN_ATM_TENDENCY3M"
        value={formData.SUM_TRAN_ATM_TENDENCY3M}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.SUM_TRAN_ATM_TENDENCY3M}
      />
      <TextField
        label="SUM_TRAN_SUP_TENDENCY1M"
        helperText={errors.SUM_TRAN_SUP_TENDENCY1M || 'Very short‑term supermarket amount trend (1 month).'}
        name="SUM_TRAN_SUP_TENDENCY1M"
        value={formData.SUM_TRAN_SUP_TENDENCY1M}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.SUM_TRAN_SUP_TENDENCY1M}
      />
      <TextField
        label="SUM_TRAN_ATM_TENDENCY1M"
        helperText={errors.SUM_TRAN_ATM_TENDENCY1M || 'Very short‑term ATM amount trend (1 month).'}
        name="SUM_TRAN_ATM_TENDENCY1M"
        value={formData.SUM_TRAN_ATM_TENDENCY1M}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.SUM_TRAN_ATM_TENDENCY1M}
      />
      <TextField
        label="CNT_TRAN_SUP_TENDENCY1M"
        helperText={errors.CNT_TRAN_SUP_TENDENCY1M || 'Very short‑term supermarket count trend (1 month).'}
        name="CNT_TRAN_SUP_TENDENCY1M"
        value={formData.CNT_TRAN_SUP_TENDENCY1M}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.CNT_TRAN_SUP_TENDENCY1M}
      />

      <TextField
        label="TURNOVER_DYNAMIC_CUR_3M"
        helperText={errors.TURNOVER_DYNAMIC_CUR_3M || 'Medium‑term trend of current account turnovers (3 months).'}
        name="TURNOVER_DYNAMIC_CUR_3M"
        value={formData.TURNOVER_DYNAMIC_CUR_3M}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.TURNOVER_DYNAMIC_CUR_3M}
      />
      <TextField
        label="CLNT_SETUP_TENOR"
        helperText={errors.CLNT_SETUP_TENOR || 'Months since the client joined the bank.'}
        name="CLNT_SETUP_TENOR"
        value={formData.CLNT_SETUP_TENOR}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.CLNT_SETUP_TENOR}
      />
      <TextField
        label="TURNOVER_DYNAMIC_PAYM_3M"
        helperText={errors.TURNOVER_DYNAMIC_PAYM_3M || 'Trend of turnovers on payment products (3 months).'}
        name="TURNOVER_DYNAMIC_PAYM_3M"
        value={formData.TURNOVER_DYNAMIC_PAYM_3M}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.TURNOVER_DYNAMIC_PAYM_3M}
      />
      <TextField
        label="TURNOVER_DYNAMIC_PAYM_1M"
        helperText={errors.TURNOVER_DYNAMIC_PAYM_1M || 'Short‑term trend of turnovers on payment products (1 month).'}
        name="TURNOVER_DYNAMIC_PAYM_1M"
        value={formData.TURNOVER_DYNAMIC_PAYM_1M}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.TURNOVER_DYNAMIC_PAYM_1M}
      />

      <TextField
        label="TRANS_AMOUNT_TENDENCY3M"
        helperText={errors.TRANS_AMOUNT_TENDENCY3M || 'Ratio of transaction amount in last 3 vs last 6 months.'}
        name="TRANS_AMOUNT_TENDENCY3M"
        value={formData.TRANS_AMOUNT_TENDENCY3M}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.TRANS_AMOUNT_TENDENCY3M}
      />
      <TextField
        label="TRANS_CNT_TENDENCY3M"
        helperText={errors.TRANS_CNT_TENDENCY3M || 'Ratio of transaction count in last 3 vs last 6 months.'}
        name="TRANS_CNT_TENDENCY3M"
        value={formData.TRANS_CNT_TENDENCY3M}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        inputMode="numeric"
        error={!!errors.TRANS_CNT_TENDENCY3M}
      />

      <TextField
        select
        label="PACK"
        name="PACK"
        value={formData.PACK}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
        error={!!errors.PACK}
        helperText={errors.PACK || 'Service package (102, 103, 104, 105).'}
      >
        <MenuItem value={102}>102</MenuItem>
        <MenuItem value={103}>103</MenuItem>
        <MenuItem value={104}>104</MenuItem>
        <MenuItem value={105}>105</MenuItem>
      </TextField>

      <Box sx={{ mt: 2, mb: 2, display: 'flex', gap: 2 }}>
      <Button
        type="submit"
        variant="contained"
        color="primary"
        disabled={loading}
        sx={{ mt: 2, mb: 2 }}
      >
        {loading ? 'Predicting...' : 'Get Prediction'}
      </Button>
      <Button
        type="button"
        variant="outlined"
        color="secondary"
        sx={{ mt: 2, mb: 2 }}
        onClick={handleReset}
        >
        New Prediction
      </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}

      {prediction && (
        <Alert
            severity={prediction.label === 'Churner' ? 'error' : 'success'}
            sx={{ mt: 2 }}
        >
            Prediction for customer <strong>{prediction.customerId}</strong>:
            {' '}
            <strong>{prediction.label}</strong>
        </Alert>
        )}
    </Box>
  );
}

export default GetPrediction;
