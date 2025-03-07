#!/bin/bash
set -e

# Start Sybase server
echo "Starting Sybase ASE server..."
/opt/sybase/ASE-16_0/install/RUN_SYBASE &
sleep 30

# Run SQL initialization scripts
echo "Initializing sample database..."
isql -Usa -Psybase123 -S$DSQUERY -i/opt/sybase/init-scripts/create_sample_db.sql

echo "Sybase initialization completed."
