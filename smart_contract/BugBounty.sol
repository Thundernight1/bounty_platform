// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

/**
 * @title BugBounty
 * @dev A simplified smart contract to manage bug bounty submissions and payouts.
 * This contract is intentionally minimal and should be reviewed and tested
 * extensively before deployment on a production network.  In a real system,
 * additional access control, dispute resolution and multi‑sig withdrawal
 * mechanisms are required.
 */
contract BugBounty {
    struct BugReport {
        address reporter;
        string description;
        uint8 severity;
        bool approved;
        bool paid;
    }

    address public owner;
    uint256 public nextReportId;
    mapping(uint256 => BugReport) public reports;

    // Modifier to restrict functions to the contract owner
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call");
        _;
    }

    constructor() {
        owner = msg.sender;
        nextReportId = 1;
    }

    /**
     * @notice Submit a bug report.
     * @param description Short description of the vulnerability.
     * @param severity A severity score (0‑10) assigned by the scanner.
     */
    function submitBug(string calldata description, uint8 severity) external {
        require(severity <= 10, "Severity must be 0‑10");
        reports[nextReportId] = BugReport({
            reporter: msg.sender,
            description: description,
            severity: severity,
            approved: false,
            paid: false
        });
        nextReportId += 1;
    }

    /**
     * @notice Approve a reported bug.  Only callable by owner.
     * @param reportId ID of the report to approve.
     */
    function approveBug(uint256 reportId) external onlyOwner {
        BugReport storage report = reports[reportId];
        require(!report.approved, "Already approved");
        report.approved = true;
    }

    /**
     * @notice Pay out a bounty for an approved bug.  Only owner can trigger.
     *        The payout amount is proportional to the severity (basic example).
     * @param reportId ID of the report to payout.
     */
    function payout(uint256 reportId) external onlyOwner {
        BugReport storage report = reports[reportId];
        require(report.approved, "Not approved");
        require(!report.paid, "Already paid");
        report.paid = true;
        uint256 reward = report.severity * 0.01 ether;
        require(address(this).balance >= reward, "Insufficient funds");
        payable(report.reporter).transfer(reward);
    }

    /**
     * @notice Allow the contract to receive funds.  Bounty pool is funded via ETH transfers.
     */
    receive() external payable {}
}