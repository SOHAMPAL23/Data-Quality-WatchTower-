/**
 * Dataset Profiler - Client-side dataset analysis and rule generation
 */

class DatasetProfiler {
    constructor() {
        this.data = null;
        this.profile = null;
        this.rules = [];
        this.visualizations = {};
    }

    /**
     * Parse CSV data using PapaParse
     */
    async parseCSV(file) {
        return new Promise((resolve, reject) => {
            Papa.parse(file, {
                header: true,
                dynamicTyping: true,
                skipEmptyLines: true,
                complete: (results) => {
                    this.data = results.data;
                    resolve(results);
                },
                error: (error) => {
                    reject(error);
                }
            });
        });
    }

    /**
     * Profile the dataset
     */
    profileDataset() {
        if (!this.data || this.data.length === 0) {
            throw new Error('No data to profile');
        }

        const profile = {
            rowCount: this.data.length,
            columnCount: Object.keys(this.data[0]).length,
            columns: {},
            patterns: {}
        };

        // Get column names
        const columns = Object.keys(this.data[0]);

        // Analyze each column
        columns.forEach(column => {
            profile.columns[column] = this.analyzeColumn(column);
        });

        // Detect patterns
        profile.patterns = this.detectPatterns(columns);

        this.profile = profile;
        return profile;
    }

    /**
     * Analyze a single column
     */
    analyzeColumn(column) {
        const columnData = this.data.map(row => row[column]);
        const nonNullData = columnData.filter(val => val !== null && val !== undefined && val !== '');

        // Null count
        const nullCount = columnData.length - nonNullData.length;
        const nullPercentage = (nullCount / columnData.length) * 100;

        // Unique count
        const uniqueValues = [...new Set(nonNullData)];
        const uniquePercentage = (uniqueValues.length / nonNullData.length) * 100;

        // Data type inference
        let dataType = 'string';
        if (nonNullData.every(val => typeof val === 'number')) {
            dataType = 'numeric';
        } else if (nonNullData.every(val => {
            if (typeof val !== 'string') return false;
            return !isNaN(Date.parse(val));
        })) {
            dataType = 'date';
        }

        // Min/Max for numeric data
        let min = null, max = null;
        if (dataType === 'numeric') {
            min = Math.min(...nonNullData);
            max = Math.max(...nonNullData);
        }

        // Length analysis for strings
        let minLength = null, maxLength = null;
        if (dataType === 'string' || dataType === 'date') {
            const lengths = nonNullData.map(val => String(val).length);
            minLength = Math.min(...lengths);
            maxLength = Math.max(...lengths);
        }

        return {
            nullCount: nullCount,
            nullPercentage: nullPercentage,
            uniqueCount: uniqueValues.length,
            uniquePercentage: uniquePercentage,
            dataType: dataType,
            min: min,
            max: max,
            minLength: minLength,
            maxLength: maxLength
        };
    }

    /**
     * Detect patterns in the data
     */
    detectPatterns(columns) {
        const patterns = {};

        columns.forEach(column => {
            const columnData = this.data.map(row => row[column]).filter(val => val !== null && val !== undefined);
            if (columnData.length === 0) return;

            patterns[column] = {
                email: this.detectEmailPattern(columnData),
                phone: this.detectPhonePattern(columnData),
                url: this.detectUrlPattern(columnData),
                date: this.detectDatePattern(columnData)
            };
        });

        return patterns;
    }

    /**
     * Pattern detection functions
     */
    detectEmailPattern(data) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const emailCount = data.filter(val => typeof val === 'string' && emailRegex.test(val)).length;
        return (emailCount / data.length) * 100;
    }

    detectPhonePattern(data) {
        const phoneRegex = /^(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$/;
        const phoneCount = data.filter(val => typeof val === 'string' && phoneRegex.test(val)).length;
        return (phoneCount / data.length) * 100;
    }

    detectUrlPattern(data) {
        const urlRegex = /^https?:\/\/(?:[-\w.])+(?:[:\d]+)?(?:\/(?:[\w\/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$/;
        const urlCount = data.filter(val => typeof val === 'string' && urlRegex.test(val)).length;
        return (urlCount / data.length) * 100;
    }

    detectDatePattern(data) {
        const dateCount = data.filter(val => {
            if (typeof val !== 'string') return false;
            return !isNaN(Date.parse(val));
        }).length;
        return (dateCount / data.length) * 100;
    }

    /**
     * Generate rules based on the profile
     */
    generateRules() {
        if (!this.profile) {
            throw new Error('Dataset must be profiled before generating rules');
        }

        const rules = [];

        Object.keys(this.profile.columns).forEach(column => {
            const colProfile = this.profile.columns[column];

            // NOT NULL rule
            if (colProfile.nullPercentage < 95) {
                rules.push({
                    type: 'NOT_NULL',
                    column: column,
                    confidence: Math.min(100, 100 - colProfile.nullPercentage),
                    severity: colProfile.nullPercentage < 10 ? 'HIGH' : colProfile.nullPercentage < 50 ? 'MEDIUM' : 'LOW'
                });
            }

            // UNIQUE rule
            if (colProfile.uniquePercentage > 90) {
                rules.push({
                    type: 'UNIQUE',
                    column: column,
                    confidence: Math.min(100, colProfile.uniquePercentage),
                    severity: colProfile.uniquePercentage > 95 ? 'HIGH' : 'MEDIUM'
                });
            }

            // IN_RANGE rule for numeric data
            if (colProfile.dataType === 'numeric' && colProfile.min !== null && colProfile.max !== null) {
                if (colProfile.min >= 0 && colProfile.max <= 1000000) {
                    rules.push({
                        type: 'IN_RANGE',
                        column: column,
                        params: {
                            min: colProfile.min,
                            max: colProfile.max
                        },
                        confidence: 80,
                        severity: 'MEDIUM'
                    });
                }
            }

            // LENGTH_RANGE rule for string data
            if ((colProfile.dataType === 'string' || colProfile.dataType === 'date') && 
                colProfile.minLength !== null && colProfile.maxLength !== null) {
                if (colProfile.maxLength - colProfile.minLength > 10 && colProfile.maxLength <= 1000) {
                    rules.push({
                        type: 'LENGTH_RANGE',
                        column: column,
                        params: {
                            min_length: colProfile.minLength,
                            max_length: colProfile.maxLength
                        },
                        confidence: 70,
                        severity: 'LOW'
                    });
                }
            }

            // REGEX rules based on detected patterns
            const colPatterns = this.profile.patterns[column];
            if (colPatterns) {
                if (colPatterns.email > 50) {
                    rules.push({
                        type: 'REGEX',
                        column: column,
                        params: {
                            pattern: '^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$'
                        },
                        confidence: Math.min(100, colPatterns.email),
                        severity: colPatterns.email > 80 ? 'HIGH' : 'MEDIUM'
                    });
                }

                if (colPatterns.phone > 50) {
                    rules.push({
                        type: 'REGEX',
                        column: column,
                        params: {
                            pattern: '^(\\+?\\d{1,3}[-.\\s]?)?\\(?\\d{3}\\)?[-.\\s]?\\d{3}[-.\\s]?\\d{4}$'
                        },
                        confidence: Math.min(100, colPatterns.phone),
                        severity: 'MEDIUM'
                    });
                }

                if (colPatterns.url > 30) {
                    rules.push({
                        type: 'REGEX',
                        column: column,
                        params: {
                            pattern: '^https?:\\/\\/(?:[-\\w.])+(?:[:\\d]+)?(?:\\/(?:[\\w\\/_.])*(?:\\?(?:[\\w&=%.])*)?(?:#(?:[\\w.])*)?)?$'
                        },
                        confidence: Math.min(100, colPatterns.url),
                        severity: 'MEDIUM'
                    });
                }
            }
        });

        this.rules = rules;
        return rules;
    }

    /**
     * Execute rules locally on the dataset
     */
    executeRulesLocally() {
        if (!this.data || this.rules.length === 0) {
            return [];
        }

        const results = [];

        this.rules.forEach(rule => {
            try {
                const result = this.executeRule(rule);
                results.push({
                    rule: rule,
                    result: result
                });
            } catch (error) {
                console.error(`Error executing rule ${rule.type} for column ${rule.column}:`, error);
                results.push({
                    rule: rule,
                    result: {
                        passed: 0,
                        failed: this.data.length,
                        failed_rows: [],
                        error: error.message
                    }
                });
            }
        });

        return results;
    }

    /**
     * Execute a single rule
     */
    executeRule(rule) {
        const column = rule.column;
        const columnData = this.data.map(row => row[column]);
        
        let passed = 0;
        let failed = 0;
        let failedRows = [];

        switch (rule.type) {
            case 'NOT_NULL':
                this.data.forEach((row, index) => {
                    if (row[column] !== null && row[column] !== undefined && row[column] !== '') {
                        passed++;
                    } else {
                        failed++;
                        failedRows.push({ index, row });
                    }
                });
                break;

            case 'UNIQUE':
                const valueCounts = {};
                columnData.forEach(val => {
                    valueCounts[val] = (valueCounts[val] || 0) + 1;
                });
                
                this.data.forEach((row, index) => {
                    const value = row[column];
                    if (valueCounts[value] === 1) {
                        passed++;
                    } else {
                        failed++;
                        failedRows.push({ index, row });
                    }
                });
                break;

            case 'IN_RANGE':
                const min = rule.params.min;
                const max = rule.params.max;
                
                this.data.forEach((row, index) => {
                    const value = row[column];
                    if (typeof value === 'number' && value >= min && value <= max) {
                        passed++;
                    } else {
                        failed++;
                        failedRows.push({ index, row });
                    }
                });
                break;

            case 'LENGTH_RANGE':
                const minLength = rule.params.min_length;
                const maxLength = rule.params.max_length;
                
                this.data.forEach((row, index) => {
                    const value = row[column];
                    const length = value !== null && value !== undefined ? String(value).length : 0;
                    if (length >= minLength && length <= maxLength) {
                        passed++;
                    } else {
                        failed++;
                        failedRows.push({ index, row });
                    }
                });
                break;

            case 'REGEX':
                const regex = new RegExp(rule.params.pattern);
                
                this.data.forEach((row, index) => {
                    const value = row[column];
                    if (typeof value === 'string' && regex.test(value)) {
                        passed++;
                    } else {
                        failed++;
                        failedRows.push({ index, row });
                    }
                });
                break;

            default:
                throw new Error(`Unsupported rule type: ${rule.type}`);
        }

        // Limit failed rows to first 10 for evidence
        failedRows = failedRows.slice(0, 10);

        return {
            passed: passed,
            failed: failed,
            failed_rows: failedRows,
            total_records: this.data.length,
            failed_count: failed,
            pass_rate: (passed / this.data.length) * 100
        };
    }

    /**
     * Calculate overall data quality score
     */
    calculateQualityScore(ruleResults) {
        if (!ruleResults || ruleResults.length === 0) {
            return 0;
        }

        const totalPassRate = ruleResults.reduce((sum, result) => sum + result.result.pass_rate, 0);
        return totalPassRate / ruleResults.length;
    }

    /**
     * Create visualizations using D3.js
     */
    createVisualizations(containerId, ruleResults) {
        // Clear existing visualizations
        d3.select(`#${containerId}`).html('');

        // Create quality score donut chart
        this.createQualityScoreDonut(containerId, ruleResults);

        // Create rule pass/fail bar chart
        this.createRuleBarChart(containerId, ruleResults);

        // Create column nulls heatmap
        this.createNullsHeatmap(containerId);
    }

    /**
     * Create quality score donut chart with improved styling
     */
    createQualityScoreDonut(containerId, ruleResults) {
        const qualityScore = this.calculateQualityScore(ruleResults);
        
        const width = 250;
        const height = 250;
        const radius = Math.min(width, height) / 2;
        
        // Create container for the chart
        const chartContainer = d3.select(`#${containerId}`)
            .append('div')
            .attr('class', 'col-md-4 mb-4')
            .append('div')
            .attr('class', 'card glassmorphic-card h-100');
        
        // Add header
        chartContainer.append('div')
            .attr('class', 'card-header')
            .html('<h6><i class="fas fa-chart-pie"></i> Quality Score</h6>');
        
        // Create SVG
        const svg = chartContainer.append('div')
            .attr('class', 'card-body text-center')
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .append('g')
            .attr('transform', `translate(${width/2},${height/2})`);
        
        const data = [qualityScore, 100 - qualityScore];
        const color = d3.scaleOrdinal()
            .domain(data)
            .range(['#28a745', '#e0e0e0']); // Green for quality, light gray for remainder
        
        const pie = d3.pie()
            .value(d => d)
            .sort(null);
        
        const arc = d3.arc()
            .innerRadius(radius * 0.6)
            .outerRadius(radius);
        
        // Add gradient definition
        const defs = svg.append('defs');
        const gradient = defs.append('linearGradient')
            .attr('id', 'greenGradient')
            .attr('x1', '0%')
            .attr('y1', '0%')
            .attr('x2', '100%')
            .attr('y2', '100%');
        
        gradient.append('stop')
            .attr('offset', '0%')
            .attr('stop-color', '#28a745');
        
        gradient.append('stop')
            .attr('offset', '100%')
            .attr('stop-color', '#218838');
        
        // Create arcs
        const arcs = svg.selectAll('path')
            .data(pie(data))
            .enter()
            .append('path')
            .attr('d', arc)
            .attr('fill', (d, i) => i === 0 ? 'url(#greenGradient)' : '#e0e0e0')
            .attr('stroke', '#fff')
            .attr('stroke-width', 2);
        
        // Add animation
        arcs.transition()
            .duration(1000)
            .attrTween('d', function(d) {
                const interpolate = d3.interpolate({startAngle: 0, endAngle: 0}, d);
                return function(t) {
                    return arc(interpolate(t));
                };
            });
        
        // Add center text
        const centerText = svg.append('g');
        
        centerText.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '0.35em')
            .attr('font-size', '24px')
            .attr('font-weight', 'bold')
            .attr('fill', '#fff')
            .text(Math.round(qualityScore) + '%');
        
        centerText.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '2em')
            .attr('font-size', '14px')
            .attr('fill', '#ccc')
            .text('Data Quality');
    }

    /**
     * Create rule pass/fail line chart with improved styling
     */
    createRuleBarChart(containerId, ruleResults) {
        // Limit to top 8 rules for better visualization
        const topRules = ruleResults.slice(0, 8);
        
        const margin = {top: 20, right: 30, bottom: 60, left: 60};
        const width = 500 - margin.left - margin.right;
        const height = 300 - margin.top - margin.bottom;
        
        // Create container for the chart
        const chartContainer = d3.select(`#${containerId}`)
            .append('div')
            .attr('class', 'col-md-8 mb-4')
            .append('div')
            .attr('class', 'card glassmorphic-card h-100');
        
        // Add header
        chartContainer.append('div')
            .attr('class', 'card-header')
            .html('<h6><i class="fas fa-chart-line"></i> Rule Pass/Fail Trends</h6>');
        
        // Create SVG
        const svg = chartContainer.append('div')
            .attr('class', 'card-body')
            .append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);
        
        // Prepare data
        const data = topRules.map((result, index) => ({
            rule: `${result.rule.type} (${result.rule.column.substring(0, 15)}${result.rule.column.length > 15 ? '...' : ''})`,
            passed: result.result.passed,
            failed: result.result.failed,
            passRate: result.result.pass_rate
        }));
        
        // Set up scales
        const x = d3.scalePoint()
            .domain(data.map(d => d.rule))
            .range([0, width]);
        
        const y = d3.scaleLinear()
            .domain([0, d3.max(data, d => Math.max(d.passed, d.failed))])
            .nice()
            .range([height, 0]);
        
        // Add grid lines
        svg.append('g')
            .attr('class', 'grid')
            .attr('transform', `translate(0,${height})`)
            .call(d3.axisBottom(x)
                .tickSize(-height)
                .tickFormat('')
            );
        
        svg.append('g')
            .attr('class', 'grid')
            .call(d3.axisLeft(y)
                .tickSize(-width)
                .tickFormat('')
            );
        
        // Add gradients for lines
        const defs = svg.append('defs');
        
        // Green gradient for passed line
        const greenGradient = defs.append('linearGradient')
            .attr('id', 'passedLineGradient')
            .attr('x1', '0%')
            .attr('y1', '0%')
            .attr('x2', '0%')
            .attr('y2', '100%');
        
        greenGradient.append('stop')
            .attr('offset', '0%')
            .attr('stop-color', '#28a745');
        
        greenGradient.append('stop')
            .attr('offset', '100%')
            .attr('stop-color', '#1e7e34');
        
        // Red gradient for failed line
        const redGradient = defs.append('linearGradient')
            .attr('id', 'failedLineGradient')
            .attr('x1', '0%')
            .attr('y1', '0%')
            .attr('x2', '0%')
            .attr('y2', '100%');
        
        redGradient.append('stop')
            .attr('offset', '0%')
            .attr('stop-color', '#dc3545');
        
        redGradient.append('stop')
            .attr('offset', '100%')
            .attr('stop-color', '#c82333');
        
        // Create line generators
        const passedLine = d3.line()
            .x(d => x(d.rule))
            .y(d => y(d.passed))
            .curve(d3.curveMonotoneX);
        
        const failedLine = d3.line()
            .x(d => x(d.rule))
            .y(d => y(d.failed))
            .curve(d3.curveMonotoneX);
        
        // Add passed line
        const passedPath = svg.append('path')
            .datum(data)
            .attr('class', 'passed-line')
            .attr('d', passedLine)
            .attr('fill', 'none')
            .attr('stroke', 'url(#passedLineGradient)')
            .attr('stroke-width', 3);
        
        // Animate passed line
        const passedPathLength = passedPath.node().getTotalLength();
        passedPath
            .attr('stroke-dasharray', passedPathLength)
            .attr('stroke-dashoffset', passedPathLength)
            .transition()
            .duration(1500)
            .attr('stroke-dashoffset', 0);
        
        // Add failed line
        const failedPath = svg.append('path')
            .datum(data)
            .attr('class', 'failed-line')
            .attr('d', failedLine)
            .attr('fill', 'none')
            .attr('stroke', 'url(#failedLineGradient)')
            .attr('stroke-width', 3);
        
        // Animate failed line
        const failedPathLength = failedPath.node().getTotalLength();
        failedPath
            .attr('stroke-dasharray', failedPathLength)
            .attr('stroke-dashoffset', failedPathLength)
            .transition()
            .duration(1500)
            .delay(500)
            .attr('stroke-dashoffset', 0);
        
        // Add circles for passed data points
        svg.selectAll('.passed-circle')
            .data(data)
            .enter()
            .append('circle')
            .attr('class', 'passed-circle')
            .attr('cx', d => x(d.rule))
            .attr('cy', d => y(d.passed))
            .attr('r', 0)
            .attr('fill', '#28a745')
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .transition()
            .duration(1000)
            .delay(1000)
            .attr('r', 5);
        
        // Add circles for failed data points
        svg.selectAll('.failed-circle')
            .data(data)
            .enter()
            .append('circle')
            .attr('class', 'failed-circle')
            .attr('cx', d => x(d.rule))
            .attr('cy', d => y(d.failed))
            .attr('r', 0)
            .attr('fill', '#dc3545')
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .transition()
            .duration(1000)
            .delay(1200)
            .attr('r', 5);
        
        // Add value labels on data points
        svg.selectAll('.passed-label')
            .data(data)
            .enter()
            .append('text')
            .attr('class', 'passed-label')
            .attr('x', d => x(d.rule))
            .attr('y', d => y(d.passed) - 15)
            .attr('text-anchor', 'middle')
            .attr('fill', '#28a745')
            .attr('font-size', '12px')
            .attr('font-weight', 'bold')
            .attr('opacity', 0)
            .text(d => d.passed)
            .transition()
            .duration(1000)
            .delay(1500)
            .attr('opacity', 1);
        
        svg.selectAll('.failed-label')
            .data(data)
            .enter()
            .append('text')
            .attr('class', 'failed-label')
            .attr('x', d => x(d.rule))
            .attr('y', d => y(d.failed) - 15)
            .attr('text-anchor', 'middle')
            .attr('fill', '#dc3545')
            .attr('font-size', '12px')
            .attr('font-weight', 'bold')
            .attr('opacity', 0)
            .text(d => d.failed)
            .transition()
            .duration(1000)
            .delay(1700)
            .attr('opacity', 1);
        
        // Add axes
        svg.append('g')
            .attr('transform', `translate(0,${height})`)
            .call(d3.axisBottom(x))
            .selectAll('text')
            .attr('transform', 'rotate(-45)')
            .style('text-anchor', 'end')
            .attr('dx', '-0.8em')
            .attr('dy', '0.15em')
            .attr('fill', '#fff');
        
        svg.append('g')
            .call(d3.axisLeft(y)
                .ticks(6)
                .tickFormat(d3.format('~s')))
            .selectAll('text')
            .attr('fill', '#fff');
        
        // Add axis labels
        svg.append('text')
            .attr('transform', `translate(${width / 2},${height + margin.bottom - 10})`)
            .attr('text-anchor', 'middle')
            .attr('fill', '#fff')
            .text('Rules');
        
        svg.append('text')
            .attr('transform', 'rotate(-90)')
            .attr('y', 0 - margin.left)
            .attr('x', 0 - (height / 2))
            .attr('dy', '1em')
            .attr('text-anchor', 'middle')
            .attr('fill', '#fff')
            .text('Record Count');
        
        // Add legend
        const legend = svg.append('g')
            .attr('transform', `translate(${width - 150}, 10)`);
        
        // Passed legend item
        legend.append('rect')
            .attr('x', 0)
            .attr('y', 0)
            .attr('width', 20)
            .attr('height', 3)
            .attr('fill', 'url(#passedLineGradient)');
        
        legend.append('text')
            .attr('x', 30)
            .attr('y', 5)
            .attr('fill', '#fff')
            .text('Passed');
        
        // Failed legend item
        legend.append('rect')
            .attr('x', 0)
            .attr('y', 20)
            .attr('width', 20)
            .attr('height', 3)
            .attr('fill', 'url(#failedLineGradient)');
        
        legend.append('text')
            .attr('x', 30)
            .attr('y', 25)
            .attr('fill', '#fff')
            .text('Failed');
    }

    /**
     * Create column nulls heatmap with improved styling
     */
    createNullsHeatmap(containerId) {
        if (!this.profile) return;
        
        const margin = {top: 30, right: 30, bottom: 100, left: 100};
        const width = 500 - margin.left - margin.right;
        const height = 300 - margin.top - margin.bottom;
        
        // Create container for the chart
        const chartContainer = d3.select(`#${containerId}`)
            .append('div')
            .attr('class', 'col-md-12 mb-4')
            .append('div')
            .attr('class', 'card glassmorphic-card h-100');
        
        // Add header
        chartContainer.append('div')
            .attr('class', 'card-header')
            .html('<h6><i class="fas fa-th"></i> Column Null Percentage Heatmap</h6>');
        
        // Create SVG
        const svg = chartContainer.append('div')
            .attr('class', 'card-body')
            .append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);
        
        // Prepare data
        const columns = Object.keys(this.profile.columns);
        const data = columns.map(column => ({
            column: column,
            nullPercentage: this.profile.columns[column].nullPercentage
        }));
        
        // Set up scales
        const x = d3.scaleBand()
            .domain(data.map(d => d.column))
            .range([0, width])
            .padding(0.1);
        
        const y = d3.scaleBand()
            .domain(['Null Percentage'])
            .range([0, height])
            .padding(0.1);
        
        // Color scale from green (low nulls) to red (high nulls)
        const color = d3.scaleLinear()
            .domain([0, 50, 100])
            .range(['#28a745', '#ffc107', '#dc3545']);
        
        // Add rectangles
        const cells = svg.selectAll()
            .data(data)
            .enter()
            .append('rect')
            .attr('x', d => x(d.column))
            .attr('y', y('Null Percentage'))
            .attr('width', x.bandwidth())
            .attr('height', y.bandwidth())
            .style('fill', d => color(d.nullPercentage))
            .attr('stroke', '#fff')
            .attr('stroke-width', 1)
            .attr('rx', 3)
            .attr('ry', 3);
        
        // Add animation
        cells.attr('opacity', 0)
            .transition()
            .duration(800)
            .attr('opacity', 1);
        
        // Add value labels
        svg.selectAll('.heatmap-label')
            .data(data)
            .enter()
            .append('text')
            .attr('class', 'heatmap-label')
            .attr('x', d => x(d.column) + x.bandwidth() / 2)
            .attr('y', y('Null Percentage') + y.bandwidth() / 2)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', d => d.nullPercentage > 50 ? '#fff' : '#000')
            .attr('font-size', '12px')
            .attr('font-weight', 'bold')
            .text(d => `${d.nullPercentage.toFixed(0)}%`);
        
        // Add tooltips
        cells.append('title')
            .text(d => `${d.column}: ${d.nullPercentage.toFixed(1)}% null`);
        
        // Add axes
        svg.append('g')
            .attr('transform', `translate(0,${height})`)
            .call(d3.axisBottom(x))
            .selectAll('text')
            .attr('transform', 'rotate(-45)')
            .style('text-anchor', 'end')
            .attr('dx', '-0.8em')
            .attr('dy', '0.15em')
            .attr('fill', '#fff');
        
        // Add color legend
        const legendWidth = 200;
        const legendHeight = 20;
        const legend = svg.append('g')
            .attr('transform', `translate(${(width - legendWidth) / 2},${-margin.top + 5})`);
        
        // Create gradient for legend
        const legendGradient = legend.append('defs')
            .append('linearGradient')
            .attr('id', 'legend-gradient')
            .attr('x1', '0%')
            .attr('y1', '0%')
            .attr('x2', '100%')
            .attr('y2', '0%');
        
        legendGradient.append('stop')
            .attr('offset', '0%')
            .attr('stop-color', '#28a745'); // Green
        
        legendGradient.append('stop')
            .attr('offset', '50%')
            .attr('stop-color', '#ffc107'); // Yellow
        
        legendGradient.append('stop')
            .attr('offset', '100%')
            .attr('stop-color', '#dc3545'); // Red
        
        legend.append('rect')
            .attr('width', legendWidth)
            .attr('height', legendHeight)
            .style('fill', 'url(#legend-gradient)')
            .attr('stroke', '#fff')
            .attr('stroke-width', 1);
        
        // Add legend labels
        legend.append('text')
            .attr('x', 0)
            .attr('y', -5)
            .attr('text-anchor', 'start')
            .attr('fill', '#fff')
            .text('0%');
        
        legend.append('text')
            .attr('x', legendWidth / 2)
            .attr('y', -5)
            .attr('text-anchor', 'middle')
            .attr('fill', '#fff')
            .text('50%');
        
        legend.append('text')
            .attr('x', legendWidth)
            .attr('y', -5)
            .attr('text-anchor', 'end')
            .attr('fill', '#fff')
            .text('100%');
        
        legend.append('text')
            .attr('x', legendWidth / 2)
            .attr('y', legendHeight + 15)
            .attr('text-anchor', 'middle')
            .attr('fill', '#fff')
            .text('Null Percentage');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DatasetProfiler;
}