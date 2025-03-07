import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Snackbar,
  Card,
  CardContent,
} from '@mui/material';
import { apiService } from '../services/apiService';

const Settings = () => {
  const [settings, setSettings] = useState({
    apiKey: '',
    enableNotifications: true,
    enableAutoAnalysis: false,
    maxConcurrentJobs: 3,
    defaultDatabaseType: 'sybase',
  });
  
  const [loading, setLoading] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState(false);
  
  useEffect(() => {
    // In a real app, this would fetch settings from the API
    // Mock loading for demonstration
    setLoading(true);
    setTimeout(() => {
      // Use the OpenAI API key from environment if available
      const apiKey = process.env.REACT_APP_OPENAI_API_KEY || '';
      setSettings({
        ...settings,
        apiKey,
      });
      setLoading(false);
    }, 500);
  }, []);
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, checked, type } = e.target;
    setSettings({
      ...settings,
      [name]: type === 'checkbox' ? checked : value,
    });
  };
  
  const handleNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    const numValue = parseInt(value, 10);
    if (!isNaN(numValue) && numValue >= 1) {
      setSettings({
        ...settings,
        [name]: numValue,
      });
    }
  };
  
  const handleSave = () => {
    setLoading(true);
    
    // In a real app, this would save settings via the API
    // Mock API call for demonstration
    setTimeout(() => {
      // Simulate successful save
      setSaveSuccess(true);
      setLoading(false);
      
      // Hide success message after 3 seconds
      setTimeout(() => {
        setSaveSuccess(false);
      }, 3000);
    }, 1000);
  };
  
  const handleCloseSnackbar = () => {
    setSaveSuccess(false);
    setSaveError(false);
  };
  
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          API Configuration
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <TextField
              label="OpenAI API Key"
              name="apiKey"
              value={settings.apiKey}
              onChange={handleChange}
              fullWidth
              type="password"
              helperText="Your OpenAI API key for LLM Agent functionality"
            />
          </Grid>
        </Grid>
        
        <Divider sx={{ my: 3 }} />
        
        <Typography variant="h6" gutterBottom>
          Application Settings
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.enableNotifications}
                  onChange={handleChange}
                  name="enableNotifications"
                />
              }
              label="Enable Notifications"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.enableAutoAnalysis}
                  onChange={handleChange}
                  name="enableAutoAnalysis"
                />
              }
              label="Enable Automatic Analysis"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              label="Max Concurrent Jobs"
              name="maxConcurrentJobs"
              type="number"
              value={settings.maxConcurrentJobs}
              onChange={handleNumberChange}
              fullWidth
              inputProps={{ min: 1, max: 10 }}
              helperText="Maximum number of concurrent analysis jobs"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              label="Default Database Type"
              name="defaultDatabaseType"
              select
              value={settings.defaultDatabaseType}
              onChange={handleChange}
              fullWidth
              SelectProps={{
                native: true,
              }}
              helperText="Default database type for new connections"
            >
              <option value="sybase">Sybase ASE</option>
              <option value="mssql">Microsoft SQL Server</option>
              <option value="oracle">Oracle</option>
              <option value="mysql">MySQL</option>
              <option value="postgresql">PostgreSQL</option>
            </TextField>
          </Grid>
        </Grid>
        
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            onClick={handleSave}
            disabled={loading}
          >
            {loading ? 'Saving...' : 'Save Settings'}
          </Button>
        </Box>
      </Paper>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                About VMigrateAgent
              </Typography>
              <Typography variant="body2" paragraph>
                VMigrateAgent is a comprehensive tool for analyzing database schemas and dependencies
                to facilitate database migration projects. It helps identify potential issues and
                complexities in your database structure.
              </Typography>
              <Typography variant="body2">
                Version: 1.0.0
              </Typography>
              <Typography variant="body2">
                Build Date: March 2025
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Information
              </Typography>
              <Typography variant="body2">
                Backend Status: Connected
              </Typography>
              <Typography variant="body2">
                Database Connectors: Sybase, MSSQL, Oracle, MySQL, PostgreSQL
              </Typography>
              <Typography variant="body2">
                LLM Agent: {settings.apiKey ? 'Configured' : 'Not Configured'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <Snackbar
        open={saveSuccess}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="success">
          Settings saved successfully!
        </Alert>
      </Snackbar>
      
      <Snackbar
        open={saveError}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="error">
          Error saving settings. Please try again.
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Settings;
