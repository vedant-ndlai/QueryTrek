FROM datagrip/sybase:16.0

# Copy initialization scripts
COPY ./init-scripts/ /opt/sybase/init-scripts/

# Set environment variables
ENV SYBASE_USER=sa
ENV SYBASE_PASSWORD=sybase123

# Expose Sybase port
EXPOSE 5000

# Run initialization script when container starts
CMD ["/bin/bash", "-c", "sh /opt/sybase/init-scripts/init.sh && tail -f /dev/null"]
