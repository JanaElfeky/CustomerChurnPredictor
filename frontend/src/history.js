// src/history.js
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  TextField,
} from '@mui/material';
import { getPredictionHistory } from './api';

function PredictionHistory() {
  const [history, setHistory] = useState([]);
  const [limit, setLimit] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

useEffect(() => {
  const fetchHistory = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getPredictionHistory(limit);
      console.log('history API response', data);  // <--- important
      // adjust this line once you see the real shape
      setHistory(Array.isArray(data) ? data : (data.predictions || []));
    } catch (err) {
      setError(err.message || 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  fetchHistory();
}, [limit]);

  const handleLimitChange = (e) => {
    const raw = e.target.value;
    if (raw === '') {
      setLimit('');
      return;
    }
    const num = Number(raw);
    const clamped = Math.min(50, Math.max(1, isNaN(num) ? 1 : num));
    setLimit(clamped);
    // optional: reload immediately if you later support ?limit=
    // loadHistory();
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Recent Predictions
      </Typography>

      <TextField
        label="How many predictions?"
        type="number"
        value={limit}
        onChange={handleLimitChange}
        inputProps={{ min: 1, max: 50 }}
        size="small"
        sx={{ mb: 2, width: 220 }}
        helperText="Choose between 1 and 50"
      />

      {loading && <CircularProgress />}
      {error && <Typography color="error">{error}</Typography>}

      {!loading && !error && (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Timestamp</TableCell>
                <TableCell>Customer ID</TableCell>
                <TableCell>Prediction</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
            {history.length === 0 ? (
                <TableRow>
                <TableCell colSpan={3} align="center">
                    No predictions yet.
                </TableCell>
                </TableRow>
            ) : (
                history.map((item) => (
                <TableRow key={item.id}>
                    <TableCell>{item.customer_id}</TableCell>
                    <TableCell
                    style={{ color: item.predicted_churn ? 'red' : 'green' }}
                    >
                    {item.predicted_churn ? 'Churner' : 'Non‑churner'}
                    </TableCell>
                </TableRow>
                ))
            )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}

export default PredictionHistory;
