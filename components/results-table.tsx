"use client"

import { useState, useMemo } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Search, ArrowUpDown, ArrowUp, ArrowDown, CheckCircle, AlertTriangle, Download } from "lucide-react"
import type { LabResult } from "@/app/page"

interface ResultsTableProps {
  data: LabResult[]
}

type SortField = keyof LabResult
type SortDirection = "asc" | "desc" | null

export function ResultsTable({ data }: ResultsTableProps) {
  const [searchTerm, setSearchTerm] = useState("")
  const [sortField, setSortField] = useState<SortField | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>(null)

  // Filter and sort data
  const processedData = useMemo(() => {
    const filtered = data.filter(
      (item) =>
        item.test_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.test_value.toLowerCase().includes(searchTerm.toLowerCase()),
    )

    if (sortField && sortDirection) {
      filtered.sort((a, b) => {
        const aValue = a[sortField]
        const bValue = b[sortField]

        if (typeof aValue === "boolean" && typeof bValue === "boolean") {
          return sortDirection === "asc"
            ? aValue === bValue
              ? 0
              : aValue
                ? 1
                : -1
            : aValue === bValue
              ? 0
              : aValue
                ? -1
                : 1
        }

        const comparison = aValue.localeCompare(bValue)
        return sortDirection === "asc" ? comparison : -comparison
      })
    }

    return filtered
  }, [data, searchTerm, sortField, sortDirection])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : prev === "desc" ? null : "asc"))
      if (sortDirection === "desc") {
        setSortField(null)
      }
    } else {
      setSortField(field)
      setSortDirection("asc")
    }
  }

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) return <ArrowUpDown className="h-4 w-4" />
    if (sortDirection === "asc") return <ArrowUp className="h-4 w-4" />
    if (sortDirection === "desc") return <ArrowDown className="h-4 w-4" />
    return <ArrowUpDown className="h-4 w-4" />
  }

  const exportToCSV = () => {
    const headers = ["Test Name", "Value", "Reference Range", "Unit", "Status"]
    const csvContent = [
      headers.join(","),
      ...processedData.map((row) =>
        [
          `"${row.test_name}"`,
          `"${row.test_value}"`,
          `"${row.bio_reference_range}"`,
          `"${row.test_unit}"`,
          `"${row.lab_test_out_of_range ? "Out of Range" : "Normal"}"`,
        ].join(","),
      ),
    ].join("\n")

    const blob = new Blob([csvContent], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = "lab-results.csv"
    link.click()
    URL.revokeObjectURL(url)
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No test results available</p>
      </div>
    )
  }

  const normalCount = data.filter((item) => !item.lab_test_out_of_range).length
  const outOfRangeCount = data.filter((item) => item.lab_test_out_of_range).length

  return (
    <div className="space-y-4">
      {/* Enhanced Summary Stats */}
      <div className="grid grid-cols-3 gap-6 p-6 bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 rounded-2xl border border-blue-100 shadow-sm">
        <div className="text-center space-y-2">
          <div className="relative">
            <div className="absolute inset-0 bg-blue-500 rounded-full blur-lg opacity-20 animate-pulse"></div>
            <div className="relative text-3xl font-bold text-blue-600 bg-white rounded-full w-16 h-16 flex items-center justify-center mx-auto shadow-lg">
              {data.length}
            </div>
          </div>
          <div className="text-sm font-semibold text-gray-700">Total Tests</div>
        </div>
        <div className="text-center space-y-2">
          <div className="relative">
            <div className="absolute inset-0 bg-green-500 rounded-full blur-lg opacity-20 animate-pulse"></div>
            <div className="relative text-3xl font-bold text-green-600 bg-white rounded-full w-16 h-16 flex items-center justify-center mx-auto shadow-lg">
              {normalCount}
            </div>
          </div>
          <div className="text-sm font-semibold text-gray-700">Normal Range</div>
        </div>
        <div className="text-center space-y-2">
          <div className="relative">
            <div className="absolute inset-0 bg-red-500 rounded-full blur-lg opacity-20 animate-pulse"></div>
            <div className="relative text-3xl font-bold text-red-600 bg-white rounded-full w-16 h-16 flex items-center justify-center mx-auto shadow-lg">
              {outOfRangeCount}
            </div>
          </div>
          <div className="text-sm font-semibold text-gray-700">Out of Range</div>
        </div>
      </div>

      {/* Search and Export */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between items-center bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-gray-200">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <Input
            placeholder="Search tests..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-12 py-3 rounded-xl border-2 border-gray-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-200 bg-white"
          />
        </div>
        <Button
          variant="outline"
          onClick={exportToCSV}
          className="bg-gradient-to-r from-green-500 to-emerald-500 text-white border-0 hover:from-green-600 hover:to-emerald-600 shadow-md hover:shadow-lg transition-all duration-200 px-6 py-3"
        >
          <Download className="h-4 w-4 mr-2" />
          Export CSV
        </Button>
      </div>

      {/* Results Table */}
      <div className="border-2 border-gray-200 rounded-2xl overflow-hidden shadow-lg bg-white">
        <Table>
          <TableHeader>
            <TableRow className="bg-gradient-to-r from-gray-50 to-blue-50 border-b-2 border-gray-200">
              <TableHead className="font-semibold">
                <Button
                  variant="ghost"
                  onClick={() => handleSort("test_name")}
                  className="h-auto p-0 font-semibold hover:bg-transparent"
                >
                  Test Name
                  {getSortIcon("test_name")}
                </Button>
              </TableHead>
              <TableHead className="font-semibold">
                <Button
                  variant="ghost"
                  onClick={() => handleSort("test_value")}
                  className="h-auto p-0 font-semibold hover:bg-transparent"
                >
                  Value
                  {getSortIcon("test_value")}
                </Button>
              </TableHead>
              <TableHead className="font-semibold">Reference Range</TableHead>
              <TableHead className="font-semibold">Unit</TableHead>
              <TableHead className="font-semibold">
                <Button
                  variant="ghost"
                  onClick={() => handleSort("lab_test_out_of_range")}
                  className="h-auto p-0 font-semibold hover:bg-transparent"
                >
                  Status
                  {getSortIcon("lab_test_out_of_range")}
                </Button>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {processedData.map((result, index) => (
              <TableRow
                key={index}
                className={`
            hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 transition-all duration-200 border-b border-gray-100
            ${index % 2 === 0 ? "bg-white" : "bg-gray-50/50"}
          `}
              >
                <TableCell className="font-medium">{result.test_name}</TableCell>
                <TableCell
                  className={
                    result.lab_test_out_of_range ? "font-semibold text-red-700" : "font-semibold text-green-700"
                  }
                >
                  {result.test_value}
                </TableCell>
                <TableCell className="text-gray-600">{result.bio_reference_range}</TableCell>
                <TableCell className="text-gray-600">{result.test_unit}</TableCell>
                <TableCell>
                  <Badge
                    variant={result.lab_test_out_of_range ? "destructive" : "default"}
                    className={`
                px-3 py-1 font-semibold shadow-sm transition-all duration-200
                ${
                  result.lab_test_out_of_range
                    ? "bg-gradient-to-r from-red-500 to-pink-500 text-white hover:from-red-600 hover:to-pink-600 shadow-red-200"
                    : "bg-gradient-to-r from-green-500 to-emerald-500 text-white hover:from-green-600 hover:to-emerald-600 shadow-green-200"
                }
              `}
                  >
                    {result.lab_test_out_of_range ? (
                      <AlertTriangle className="h-3 w-3 mr-1" />
                    ) : (
                      <CheckCircle className="h-3 w-3 mr-1" />
                    )}
                    {result.lab_test_out_of_range ? "Out of Range" : "Normal"}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {processedData.length === 0 && searchTerm && (
        <div className="text-center py-8 text-gray-500">
          <p>No results found for "{searchTerm}"</p>
          <Button variant="link" onClick={() => setSearchTerm("")} className="mt-2">
            Clear search
          </Button>
        </div>
      )}
    </div>
  )
}
