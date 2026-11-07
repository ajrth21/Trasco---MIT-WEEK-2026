/**
 * TRASCO Dashboard Types
 * Sourced directly from @trasco/shared-types for unified ecosystem contracts
 */

import { SecurityOverviewResponse } from '@trasco/shared-types';

export * from '@trasco/shared-types';

// Backward compatibility alias for dashboard components
export type SecurityOverviewData = SecurityOverviewResponse;
