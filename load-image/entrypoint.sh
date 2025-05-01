#!/usr/bin/env bash
set -e
stress-ng --cpu ${STRESS_CPU:-2} --memory ${STRESS_MEM:-128M} --vm-bytes ${STRESS_MEM:-128M} --vm-keep