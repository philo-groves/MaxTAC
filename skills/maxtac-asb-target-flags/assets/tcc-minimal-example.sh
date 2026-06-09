#!/bin/bash
# tcc_flag_wrapper.sh — Demonstration script for TCC Target Flag
echo "Checking SIP status..."
csrutil status

echo "Resetting integrity flag..."
tccutil flag reset

echo "Running your poc here..."
./tcc_flag_poc.sh

echo "Checking integrity flag status..."
tccutil flag check