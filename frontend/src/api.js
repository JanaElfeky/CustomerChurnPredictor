const API_BASE = 'http://localhost:5001/api';

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
    probability: rawProb,   // remove if you don’t want to show it
  };
};


// export const getPredictionHistory = async (limit = 20) => {
//   const params = new URLSearchParams({ limit: limit });
//   const response = await fetch(`/api/history/recent?${params}`);
//   if (!response.ok) {
//     throw new Error(`HTTP error! status: ${response.status}`);
//   }
//   return response.json();
// };

export async function getPredictionHistory(limit) {
  const url = `${API_BASE}/history/recent?limit=${limit}`;
  console.log('Fetching history from', url);
  const res = await fetch(url);
  const text = await res.text();
  console.log('Raw response text:', text.slice(0, 200)); // first 200 chars
  return JSON.parse(text);  // TEMP: parse manually so you see the raw HTML if it’s wrong
}

export const submitFeedback = async (feedbacks) => {
  // map from form rows to API payload
  const labels = feedbacks.map((row) => ({
    customer_id: Number(row.CustomerID),
    target: row.churned === true, // true/false
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

// if you ever need to send a single label instead:
// export const submitSingleFeedback = async (label) => {
//   const res = await fetch(`${API_BASE}/feedback/add-label`, {
//     method: 'POST',
//     headers: { 'Content-Type': 'application/json' },
//     body: JSON.stringify(label),
//   });
//   if (!res.ok) throw new Error('Feedback submission failed');
//   return res.json();
// };



// const USE_MOCK = true; // set to false later when your real APIs are ready
// const API_BASE = 'http://localhost:8000';

// export const predictChurn = async (userData) => {
//   if (USE_MOCK) {
//     // fake response
//     return {
//       label: Number(userData.age) > 40 ? 'Churner' : 'Non-churner',
//       churnProbability: Number(userData.age) > 40 ? 0.78 : 0.22,
//     };
//   }

//   const response = await fetch(`${API_BASE}/predict`, {
//     method: 'POST',
//     headers: { 'Content-Type': 'application/json' },
//     body: JSON.stringify(userData),
//   });
//   if (!response.ok) throw new Error('Prediction failed');
//   return response.json();
// };

// export const getPredictionHistory = async () => {
//   if (USE_MOCK) {
//     return {
//       predictions: [
//         {
//           timestamp: new Date().toISOString(),
//           user_id: '123',
//           age: 45,
//           tenure: 24,
//           balance: 50000,
//           num_products: 2,
//           credit_score: 650,
//           label: 'Churner',
//           churnProbability: 0.81,
//         },
//         {
//           timestamp: new Date().toISOString(),
//           user_id: '456',
//           age: 30,
//           tenure: 12,
//           balance: 20000,
//           num_products: 1,
//           credit_score: 720,
//           label: 'Non-churner',
//           churnProbability: 0.12,
//         },
//       ],
//     };
//   }

//   const response = await fetch(`${API_BASE}/history?limit=20`);
//   if (!response.ok) throw new Error('Failed to load history');
//   return response.json();
// };

// export const submitFeedback = async (feedbackList) => {
//   if (USE_MOCK) {
//     console.log('Mock feedback received:', feedbackList);
//     return { status: 'ok' };
//   }

//   const response = await fetch(`${API_BASE}/feedback`, {
//     method: 'POST',
//     headers: { 'Content-Type': 'application/json' },
//     body: JSON.stringify({ feedbacks: feedbackList }),
//   });
//   if (!response.ok) throw new Error('Feedback submission failed');
//   return response.json();
// };
