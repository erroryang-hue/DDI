import React, { useState, useEffect, useRef } from 'react'

interface DrugOption {
  name: string
  generic_name?: string
  drug_class?: string
  atc_class?: string
  half_life?: number
}

interface DrugAutocompleteProps {
  value: string
  onChange: (value: string) => void
  label?: string
  placeholder?: string
}

export default function DrugAutocomplete({ value, onChange, label = 'Drug', placeholder = 'Enter drug name' }: DrugAutocompleteProps) {
  const [drugs, setDrugs] = useState<DrugOption[]>([])
  const [filteredDrugs, setFilteredDrugs] = useState<DrugOption[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Fetch drugs list on mount
  useEffect(() => {
    const fetchDrugs = async () => {
      try {
        setIsLoading(true)
        const response = await fetch('http://localhost:8000/api/v1/drugs')
        const data = await response.json()
        setDrugs(data.drugs || [])
      } catch (error) {
        console.error('Failed to fetch drugs:', error)
      } finally {
        setIsLoading(false)
      }
    }
    fetchDrugs()
  }, [])

  // Filter drugs based on input
  useEffect(() => {
    if (!value) {
      setFilteredDrugs(drugs.slice(0, 10))
      return
    }
    const filtered = drugs.filter(
      drug =>
        drug.name.toLowerCase().includes(value.toLowerCase()) ||
        drug.generic_name?.toLowerCase().includes(value.toLowerCase()) ||
        drug.drug_class?.toLowerCase().includes(value.toLowerCase())
    )
    setFilteredDrugs(filtered.slice(0, 10))
  }, [value, drugs])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node) && 
          inputRef.current && !inputRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div className="drug-autocomplete-wrapper">
      <label>{label}</label>
      <div className="drug-autocomplete-container">
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setIsOpen(true)}
          placeholder={placeholder}
          disabled={isLoading}
          className="drug-autocomplete-input"
        />
        {isLoading && <span className="loading-spinner">⟳</span>}
        {isOpen && filteredDrugs.length > 0 && (
          <div ref={dropdownRef} className="drug-autocomplete-dropdown">
            {filteredDrugs.map((drug, idx) => (
              <div
                key={idx}
                className="drug-option"
                onClick={() => {
                  onChange(drug.name)
                  setIsOpen(false)
                }}
              >
                <div className="drug-name">{drug.name}</div>
                <div className="drug-info">
                  {drug.generic_name && <span>{drug.generic_name}</span>}
                  {drug.drug_class && <span>{drug.drug_class}</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
