#!/usr/bin/env bash
set -e
cd /tmp
stress-ng --cpu "${STRESS_CPU:-2}" --vm 1 --vm-bytes "${STRESS_MEM:-128M}" --vm-keep