const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

export const predictChurn = async (features) => {
  const res = await fetch(`${API_BASE}/prediction/single`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(features),
  });
  if (!res.ok) throw new Error('Prediction request failed');

  const data = await res.json();
  if (!data.success || !data.prediction) {
    throw new Error(data.error || 'Prediction failed');
  }

  const rawPred = data.prediction.predictions?.[0];
  const rawProb = data.prediction.probabilities?.[0];

  return {
    customerId: data.customer_id,
    label: rawPred ? 'Churner' : 'Non‑churner',
  };
};

export async function getPredictionHistory(limit) {
  const url = `${API_BASE}/history/recent?limit=${limit}`;
  console.log('Fetching history from', url);
  const res = await fetch(url);
  const text = await res.text();
  console.log('Raw response text:', text.slice(0, 200)); 
  return JSON.parse(text); 
}

export const submitFeedback = async (feedbacks) => {
  const labels = feedbacks.map((row) => ({
    customer_id: Number(row.CustomerID),
    target: row.churned === true, 
  }));

const res = await fetch(`${API_BASE}/feedback/batch-labels`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ labels }),
  });

  if (!res.ok) throw new Error('Failed to submit feedback');
  const data = await res.json();
  if (!data.success) throw new Error(data.error || 'Failed to submit feedback');
  return data;
};

