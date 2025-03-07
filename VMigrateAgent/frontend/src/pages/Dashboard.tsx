import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Box,
  CircularProgress,
  Paper,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import StorageIcon from '@mui/icons-material/Storage';
import SchemaIcon from '@mui/icons-material/Schema';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import HistoryIcon from '@mui/icons-material/History';
import { apiService } from '../services/apiService';

// Define types for our dashboard data
interface ActivityItem {
  id: number;
  action: string;
  database: string;
  timestamp: string;
}

interface DashboardStats {
  databaseCount: number;
  schemaCount: number;
  analysisCount: number;
  recentActivities: ActivityItem[];
}

const Dashboard = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats>({
    databaseCount: 0,
    schemaCount: 0,
    analysisCount: 0,
    recentActivities: [],
  });

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        // In a real app, this would be an API call
        // const response = await apiService.getDashboardStats();
        // setStats(response.data);
        
        // Mock data for now
        setTimeout(() => {
          setStats({
            databaseCount: 3,
            schemaCount: 5,
            analysisCount: 2,
            recentActivities: [
              { id: 1, action: 'Schema extracted', database: 'SampleDB', timestamp: '2025-03-07T08:30:00' },
              { id: 2, action: 'Dependency analysis completed', database: 'SampleDB', timestamp: '2025-03-07T08:45:00' },
              { id: 3, action: 'Connection established', database: 'TestDB', timestamp: '2025-03-06T14:20:00' },
            ],
          });
          setLoading(false);
        }, 1000);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <StorageIcon fontSize="large" color="primary" />
                <Typography variant="h5" ml={1}>
                  Databases
                </Typography>
              </Box>
              <Typography variant="h3" align="center">
                {stats.databaseCount}
              </Typography>
              <Typography variant="body2" color="text.secondary" align="center">
                Connected databases
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" onClick={() => navigate('/connect')}>
                Connect New
              </Button>
            </CardActions>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <SchemaIcon fontSize="large" color="primary" />
                <Typography variant="h5" ml={1}>
                  Schemas
                </Typography>
              </Box>
              <Typography variant="h3" align="center">
                {stats.schemaCount}
              </Typography>
              <Typography variant="body2" color="text.secondary" align="center">
                Extracted schemas
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" onClick={() => navigate('/schema')}>
                View Schemas
              </Button>
            </CardActions>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <AnalyticsIcon fontSize="large" color="primary" />
                <Typography variant="h5" ml={1}>
                  Analyses
                </Typography>
              </Box>
              <Typography variant="h3" align="center">
                {stats.analysisCount}
              </Typography>
              <Typography variant="body2" color="text.secondary" align="center">
                Completed analyses
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" onClick={() => navigate('/analysis')}>
                View Analyses
              </Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>
      
      <Paper elevation={2} sx={{ p: 2 }}>
        <Box display="flex" alignItems="center" mb={2}>
          <HistoryIcon color="primary" />
          <Typography variant="h6" ml={1}>
            Recent Activity
          </Typography>
        </Box>
        <List>
          {stats.recentActivities.length > 0 ? (
            stats.recentActivities.map((activity: ActivityItem, index: number) => (
              <React.Fragment key={activity.id}>
                <ListItem>
                  <ListItemText
                    primary={`${activity.action} - ${activity.database}`}
                    secondary={formatDate(activity.timestamp)}
                  />
                </ListItem>
                {index < stats.recentActivities.length - 1 && <Divider />}
              </React.Fragment>
            ))
          ) : (
            <ListItem>
              <ListItemText primary="No recent activity" />
            </ListItem>
          )}
        </List>
      </Paper>
      
      <Box mt={4}>
        <Typography variant="h5" gutterBottom>
          Quick Actions
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              variant="contained"
              fullWidth
              startIcon={<StorageIcon />}
              onClick={() => navigate('/connect')}
            >
              Connect Database
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              variant="contained"
              fullWidth
              startIcon={<SchemaIcon />}
              onClick={() => navigate('/schema')}
            >
              Extract Schema
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              variant="contained"
              fullWidth
              startIcon={<AnalyticsIcon />}
              onClick={() => navigate('/analysis')}
            >
              Analyze Dependencies
            </Button>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

export default Dashboard;
