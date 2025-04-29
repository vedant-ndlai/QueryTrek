import React, { useState } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Select,
  MenuItem,
  ListSubheader,
  FormControl,
  InputLabel,
  Typography,
  Alert,
  CircularProgress,
  Grid,
} from '@mui/material';
import { apiService } from '../services/apiService';

const CodeConverter = () => {
  const [sourceCode, setSourceCode] = useState('');
  const [sourceLanguage, setSourceLanguage] = useState('');
  const [targetLanguage, setTargetLanguage] = useState('');
  const [convertedCode, setConvertedCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const databaseLanguages = {
    sql: ['MySQL', 'PostgreSQL', 'Oracle', 'SQL Server', 'SQLite'],
    nosql: ['MongoDB', 'Cassandra', 'CouchDB', 'Neo4j'],
    others: ['GraphQL', 'SPARQL']
  };

  const allLanguages = Object.values(databaseLanguages).flat();

  const handleConvert = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiService.convertQuery({
        source_query: sourceCode,
        source_language: sourceLanguage,
        target_language: targetLanguage,
      });

      if (response.data.success) {
        setConvertedCode(response.data.converted_query);
      } else {
        setError(response.data.error || 'Failed to convert query');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'An error occurred while converting the query');
      console.error('Query conversion error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Database Query Converter
      </Typography>
      <Typography variant="body1" color="textSecondary" sx={{ mb: 3 }}>
        Convert queries between different database languages (SQL, NoSQL, and more)
      </Typography>
      <Paper elevation={3}>
        <Box p={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Source Database</InputLabel>
                <Select
                  value={sourceLanguage}
                  label="Source Database"
                  onChange={(e) => setSourceLanguage(e.target.value)}
                >
                  {Object.entries(databaseLanguages).map(([category, langs]) => [
                    <ListSubheader key={category}>
                      {category.toUpperCase()}
                    </ListSubheader>,
                    ...langs.map((lang) => (
                      <MenuItem key={lang} value={lang}>
                        {lang}
                      </MenuItem>
                    ))
                  ])}
                </Select>
              </FormControl>
              <TextField
                fullWidth
                multiline
                rows={12}
                label="Source Query"
                value={sourceCode}
                onChange={(e) => setSourceCode(e.target.value)}
                variant="outlined"
                sx={{ mb: 2 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Target Database</InputLabel>
                <Select
                  value={targetLanguage}
                  label="Target Database"
                  onChange={(e) => setTargetLanguage(e.target.value)}
                >
                  {Object.entries(databaseLanguages).map(([category, langs]) => [
                    <ListSubheader key={category}>
                      {category.toUpperCase()}
                    </ListSubheader>,
                    ...langs.map((lang) => (
                      <MenuItem key={lang} value={lang}>
                        {lang}
                      </MenuItem>
                    ))
                  ])}
                </Select>
              </FormControl>
              <TextField
                fullWidth
                multiline
                rows={12}
                label="Converted Query"
                value={convertedCode}
                variant="outlined"
                InputProps={{
                  readOnly: true,
                }}
                sx={{ mb: 2 }}
              />
            </Grid>
            <Grid item xs={12}>
              <Box display="flex" justifyContent="center">
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleConvert}
                  disabled={!sourceCode || !sourceLanguage || !targetLanguage || loading}
                  sx={{ minWidth: 200 }}
                >
                  {loading ? <CircularProgress size={24} /> : 'Convert Query'}
                </Button>
              </Box>
            </Grid>
          </Grid>
          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </Box>
      </Paper>
    </Box>
  );
};

export default CodeConverter;
