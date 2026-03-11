/**
 * BMA Filings - Tier-Based Access Control System
 * Manages feature access and data filtering based on user tier
 * Tiers: free, analyst, custom
 */

// ========================
// TIER FEATURE DEFINITIONS
// ========================

const TIER_FEATURES = {
    free: {
        name: 'Free',
        maxCompanies: 10,
        availableYears: [2023],
        canExport: false,
        canViewYoY: false,
        canViewFullComparison: false,
        canAccessReviewConsole: false,
        description: 'Dashboard view only'
    },
    analyst: {
        name: 'Analyst',
        maxCompanies: 40,
        availableYears: [2023, 2024],
        canExport: true,
        canViewYoY: true,
        canViewFullComparison: true,
        canAccessReviewConsole: false,
        description: 'Full dashboard with exports'
    },
    custom: {
        name: 'Custom',
        maxCompanies: 40,
        availableYears: [2023, 2024],
        canExport: true,
        canViewYoY: true,
        canViewFullComparison: true,
        canAccessReviewConsole: true,
        description: 'Everything including review console'
    }
};

// ========================
// TIER ACCESS CONTROL CLASS
// ========================

class TierAccessControl {
    constructor(userTier = 'free') {
        this.userTier = userTier;
        this.features = TIER_FEATURES[userTier];

        // Store in sessionStorage for persistence across pages
        sessionStorage.setItem('userTier', userTier);
    }

    /**
     * Determine if user can access a specific company
     * @param {string} company - Company name
     * @param {array} selectedCompanies - Currently selected companies
     * @returns {boolean}
     */
    canAccessCompany(company, selectedCompanies = []) {
        if (selectedCompanies.length >= this.features.maxCompanies) {
            return selectedCompanies.includes(company);
        }
        return true;
    }

    /**
     * Determine if user can access a specific year
     * @param {number} year - Year (e.g., 2023, 2024)
     * @returns {boolean}
     */
    canAccessYear(year) {
        return this.features.availableYears.includes(parseInt(year));
    }

    /**
     * Get list of companies user can access
     * @param {array} allCompanies - All available companies
     * @returns {array} Filtered list of accessible companies
     */
    getAccessibleCompanies(allCompanies) {
        return allCompanies.slice(0, this.features.maxCompanies);
    }

    /**
     * Get list of years user can access
     * @param {array} allYears - All available years
     * @returns {array} Filtered list of accessible years
     */
    getAccessibleYears(allYears) {
        return allYears.filter(y => this.features.availableYears.includes(y));
    }

    /**
     * Check if user can export data
     * @returns {boolean}
     */
    canExport() {
        return this.features.canExport;
    }

    /**
     * Check if user can view year-over-year charts
     * @returns {boolean}
     */
    canViewYoY() {
        return this.features.canViewYoY;
    }

    /**
     * Check if user can view full comparison table
     * @returns {boolean}
     */
    canViewFullComparison() {
        return this.features.canViewFullComparison;
    }

    /**
     * Check if user can access review console
     * @returns {boolean}
     */
    canAccessReviewConsole() {
        return this.features.canAccessReviewConsole;
    }

    /**
     * Get tier information
     * @returns {object} Tier features object
     */
    getTierInfo() {
        return this.features;
    }

    /**
     * Get maximum number of companies for this tier
     * @returns {number}
     */
    getMaxCompanies() {
        return this.features.maxCompanies;
    }

    /**
     * Check if tier is unlimited (analyst and custom)
     * @returns {boolean}
     */
    isUnlimited() {
        return this.features.maxCompanies === 40;
    }
}

// ========================
// GLOBAL TIER INSTANCE
// ========================

let tierAccess = null;

/**
 * Initialize tier access control from sessionStorage
 * @returns {TierAccessControl} Tier access instance
 */
function initializeTierAccess() {
    const storedTier = sessionStorage.getItem('userTier') || 'free';
    tierAccess = new TierAccessControl(storedTier);
    return tierAccess;
}

/**
 * Set user tier and reinitialize
 * @param {string} tier - Tier name (free, analyst, custom)
 * @returns {TierAccessControl} Updated tier access instance
 */
function setUserTier(tier) {
    if (!TIER_FEATURES[tier]) {
        console.error(`Invalid tier: ${tier}`);
        return tierAccess;
    }
    sessionStorage.setItem('userTier', tier);
    tierAccess = new TierAccessControl(tier);
    return tierAccess;
}

/**
 * Get current user tier
 * @returns {string} Current tier name
 */
function getCurrentTier() {
    return sessionStorage.getItem('userTier') || 'free';
}

/**
 * Get all tier options for UI display
 * @returns {array} Array of tier objects with metadata
 */
function getAllTiers() {
    return Object.entries(TIER_FEATURES).map(([key, value]) => ({
        id: key,
        ...value
    }));
}

/**
 * Check if feature is available for current tier
 * @param {string} featureName - Feature name (e.g., 'canExport', 'canViewYoY')
 * @returns {boolean}
 */
function hasFeature(featureName) {
    if (!tierAccess) {
        tierAccess = initializeTierAccess();
    }
    return tierAccess.features[featureName] === true;
}
