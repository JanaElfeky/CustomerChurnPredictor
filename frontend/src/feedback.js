import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
} from '@mui/material';
import { submitFeedback } from './api';

function FeedbackForm() {
  const [feedbacks, setFeedbacks] = useState([{ CustomerID: '', churned: '' }]);
  const [rowErrors, setRowErrors] = useState([]);      // per‑row errors
  const [globalError, setGlobalError] = useState('');  // top message
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const addRow = () => {
    setFeedbacks((prev) => [...prev, { CustomerID: '', churned: '' }]);
    setRowErrors((prev) => [...prev, {}]);
  };

  const removeRow = (index) => {
    setFeedbacks((prev) => prev.filter((_, i) => i !== index));
    setRowErrors((prev) => prev.filter((_, i) => i !== index));
  };

  const handleInputChange = (index, field, value) => {
    setFeedbacks((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], [field]: value };
      return copy;
    });
  };

  const validate = () => {
    const newErrors = feedbacks.map((row) => {
      const e = {};
      if (row.CustomerID === '') {
        e.CustomerID = 'Customer ID is required';
      } else if (!/^\d+$/.test(row.CustomerID)) {
        e.CustomerID = 'Customer ID must be a whole number';
      }
      if (row.churned === '' || row.churned === null) {
        e.churned = 'Please select churn status';
      }
      return e;
    });

    setRowErrors(newErrors);
    return newErrors.every((e) => Object.keys(e).length === 0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setGlobalError('');
    setSuccess('');

    if (!validate()) {
      setGlobalError('Please fix the highlighted fields.');
      return;
    }

    setLoading(true);
    try {
      await submitFeedback(feedbacks);
      setSuccess('Feedback submitted successfully!');
      setFeedbacks([{ CustomerID: '', churned: '' }]);
      setRowErrors([]);
    } catch (err) {
      setGlobalError(err.message || 'Feedback submission failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} noValidate>
      <Typography variant="h6" gutterBottom>
        Submit Feedback for Online Learning
      </Typography>

      {feedbacks.map((row, index) => (
        <Box
          key={index}
          sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}
        >
          <TextField
            label="Customer ID"
            value={row.CustomerID}
            onChange={(e) => handleInputChange(index, 'CustomerID', e.target.value)}
            fullWidth
            required
            inputMode="numeric"
            error={!!(rowErrors[index] && rowErrors[index].CustomerID)}
            helperText={rowErrors[index] && rowErrors[index].CustomerID}
          />
          <FormControl
            sx={{ minWidth: 140 }}
            required
            error={!!(rowErrors[index] && rowErrors[index].churned)}
          >
            <InputLabel>Churned?</InputLabel>
            <Select
              value={row.churned}
              label="Churned?"
              onChange={(e) => handleInputChange(index, 'churned', e.target.value)}
            >
              <MenuItem value={true}>Yes</MenuItem>
              <MenuItem value={false}>No</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            color="error"
            onClick={() => removeRow(index)}
            disabled={feedbacks.length === 1}
          >
            Remove
          </Button>
        </Box>
      ))}

      <Box sx={{ mt: 2, mb: 2, display: 'flex', gap: 2 }}>
        <Button type="submit" variant="contained" color="secondary" disabled={loading}>
          {loading ? 'Submitting...' : 'Submit Feedback'}
        </Button>

        <Button variant="outlined" onClick={addRow}>
          Add Another Customer
        </Button>
      </Box>

      {globalError && <Alert severity="error" sx={{ mt: 2 }}>{globalError}</Alert>}
      {success && <Alert severity="success" sx={{ mt: 2 }}>{success}</Alert>}
    </Box>
  );
}

export default FeedbackForm;
