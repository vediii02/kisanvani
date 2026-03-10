import * as React from "react"
import { Input } from "./input"

const PhoneInput = React.forwardRef(({ value, onChange, ...props }, ref) => {
    const handleChange = (e) => {
        let val = e.target.value;

        // Always ensure it starts with +91
        if (!val.startsWith("+91")) {
            // If they try to delete +, 9, or 1, bring it back
            val = "+91" + val.replace(/^\+?9?1?/, "").replace(/\D/g, "");
        }

        const prefix = "+91";
        // Extract everything after +91, remove non-digits, limit to 10
        const rest = val.slice(prefix.length).replace(/\D/g, "").slice(0, 10);

        const finalValue = prefix + rest;

        if (onChange) {
            onChange({
                target: {
                    ...e.target,
                    value: finalValue
                }
            });
        }
    };

    const handleKeyDown = (e) => {
        // Prevent backspacing into the +91 prefix
        if (e.key === "Backspace" && (value === undefined || value.length <= 3)) {
            e.preventDefault();
        }
        // Prevent delete key if it would mess up prefix (less common for mobile/simple inputs but good for safety)
        if (e.key === "Delete" && (value === undefined || value.length <= 3)) {
            e.preventDefault();
        }
    };

    // Ensure value is at least +91 if empty
    const displayValue = value && value.startsWith("+91") ? value : "+91";

    return (
        <Input
            {...props}
            type="tel"
            ref={ref}
            value={displayValue}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="+919876543210"
            maxLength={13} // +91 + 10 digits
        />
    );
});

PhoneInput.displayName = "PhoneInput"

export { PhoneInput }
