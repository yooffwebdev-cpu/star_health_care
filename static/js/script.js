document.addEventListener('DOMContentLoaded', function () {
    // DOM Elements
    const applyNowBtn = document.getElementById('applyNowBtn');
    const modal = document.getElementById('applicationModal');
    const closeBtn = document.querySelector('.close-btn');
    const loanForm = document.getElementById('loanForm');
    const viewPlanBtn = document.getElementById('viewPlanBtn');

    // Open Modal
    applyNowBtn.addEventListener('click', function () {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden'; // Prevent scrolling
    });

    // Close Modal
    closeBtn.addEventListener('click', closeModal);
    window.addEventListener('click', function (event) {
        if (event.target == modal) {
            closeModal();
        }
    });

    function closeModal() {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto'; // Enable scrolling
    }


    // Handle Lead Form Submission
    loanForm.addEventListener('submit', function (e) {
        e.preventDefault(); // Prevent page reload

        // Gather Data
        const formData = {
            name: document.getElementById('name').value,
            phone: document.getElementById('phone').value,
            age: document.getElementById('age').value
        };

        // Validate (Basic)
        if (!formData.name || !formData.phone || !formData.age) {
            alert('Please fill all fields');
            return;
        }

        // Change button state to loading
        const originalBtnText = viewPlanBtn.innerHTML;
        viewPlanBtn.innerHTML = 'Sending... <i class="fas fa-spinner fa-spin"></i>';
        viewPlanBtn.disabled = true;

        // Send to Backend
        fetch('/submit_lead', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        })
            .then(async response => {
                if (!response.ok) {
                    const text = await response.text();
                    let errorMsg;
                    try {
                        const data = JSON.parse(text);
                        errorMsg = data.message || `Server error: ${response.status}`;
                    } catch (e) {
                        errorMsg = `Server error ${response.status}: ${text.substring(0, 100)}`;
                    }
                    throw new Error(errorMsg);
                }
                return await response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    // If there's an error message inside success (like email failed), alert it but still show plans
                    if (data.message.includes('failed')) {
                        alert('Note: ' + data.message);
                    }

                    // Success - Show Plans
                    const modalContent = document.querySelector('.modal-content');
                    modalContent.innerHTML = `
                    <span class="close-btn" onclick="document.getElementById('applicationModal').style.display='none'">&times;</span>
                    <div class="plans-container" style="padding: 10px;">
                        <h2 style="color: #004c8f; text-align: center; margin-bottom: 20px;">Star Health Plans for You</h2>
                        <div class="plan-card" style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 5px solid #004c8f;">
                            <h3 style="margin: 0; color: #333;">Family Health Optima</h3>
                            <p style="margin: 5px 0;">Sum Insured: <b>up to ₹25 Lacs</b></p>
                            <p style="margin: 5px 0;">Coverage: <b>Individual & Family</b></p>
                            <button class="cta-btn" style="width: 100%; margin-top: 10px; padding: 8px;">View Details</button>
                        </div>
                        <div class="plan-card" style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 5px solid #ed1c24;">
                            <h3 style="margin: 0; color: #333;">Star Comprehensive</h3>
                            <p style="margin: 5px 0;">Sum Insured: <b>up to ₹1 Crore</b></p>
                            <p style="margin: 5px 0;">Coverage: <b>Whole Life</b></p>
                            <button class="cta-btn" style="width: 100%; margin-top: 10px; padding: 8px; background-color: #004c8f;">View Details</button>
                        </div>
                        <p style="font-size: 0.7rem; text-align: center; color: #888;">*Rates are indicative. T&C Apply.</p>
                    </div>
                `;
                } else {
                    throw new Error(data.message);
                }
            })
            .catch((error) => {
                console.error('Fetch Error:', error);
                alert('Debug Info: ' + error.message);
                viewPlanBtn.innerHTML = originalBtnText;
                viewPlanBtn.disabled = false;
            });
    });
});
