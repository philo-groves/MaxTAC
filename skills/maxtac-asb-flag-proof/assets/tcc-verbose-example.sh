#!/bin/bash
# tcc_flag_wrapper.sh — Demonstration script for TCC Target Flag

echo "Checking SIP status..."
sip_output=$(csrutil status 2>&1)
echo "$sip_output"

if [[ ! $sip_output == *"System Integrity Protection status: enabled"* ]]; then
    echo "ERROR: SIP is not enabled."
    exit 1
fi

echo "Resetting integrity flag..."
if ! tccutil flag reset; then
    echo "ERROR: Failed to reset integrity flag."
    exit 1
fi

echo "Running your poc here..."
./tcc_poc.sh

echo "Checking integrity flag status..."
tccutil flag check