# Magnetic Source Localization with Magnetometer Arrays
## Lab Research Update: Simulation, Array Architecture & Inversion Pipeline

**Audience:** Research Advisor (Professor) & Postdoctoral Colleagues (Sensor Hardware Team)  
**Presenter's Role:** Simulation, Array Architecture Optimization, Inversion Algorithms & Test Rig Design  
**Key Collaboration Theme:** Connecting physical sensor hardware to system-level 3D localization, de-risking stationary benchtop tests, and building an Arduino linear stage for synthetic aperture tracking.

---

### Executive Overview & Strategic Narrative for the Lab Meeting

- **Current Lab Status:** The hardware postdocs are currently testing stationary measurements with newly fabricated/shielded magnetometers. This is critical for noise floor characterization, DC offset calibration, and axis alignment.
- **My Core Contributions:**
  1. **Guiding Physical Array Sizing & Geometry:**
     - Proved mathematically that optimal array conditioning occurs when the aperture-to-depth ratio is **$L/z \approx 1.0 - 2.0$** (e.g., $L \approx 40-60\text{ cm}$ for a $0.5\text{ m}$ benchtop test depth).
     - Proved that spacing sensors widely ($\sim 20-25\text{ cm}$) protects against the horizontal dipole zero-field null ($B_z = 0$), expanding horizontal detection range from **$0.74\text{ m} \to 2.05\text{ m}$**.
  2. **Establishing Hardware-Grounded Detection Limits:**
     - Derived the analytical detection horizon for the team's $10\text{ nT}$ sensor noise floor: **$r_{\max} = 2.71\text{ m}$** for a $1\text{ A}\cdot\text{m}^2$ test dipole.
     - Quantified the fundamental physics bottleneck: sensor signal falls off as **$1/r^3$** ($8\times$ drop per distance doubling), but spatial triangulation gradient falls off as **$1/r^4$** ($16\times$ drop).
  3. **De-Risking Stationary Benchtop Testing (The Static Ambiguity Trap):**
     - Discovered a critical mathematical trap: a stationary $3\times 3$ planar array cannot distinguish a centered vertical magnet from an offset, tilted magnet. The average discrepancy across all 9 sensors is **only $3.07\text{ nT}$** (worst single sensor is $6.5\text{ nT}$), which is completely buried inside our **$10\text{ nT}$ hardware noise floor**.
     - If the lab attempts 6-DoF localization using purely stationary measurements, the solver will produce phantom positions and fail to converge uniquely.
  4. **The Actionable Solution: Building an Arduino Linear Stage (Synthetic Aperture):**
     - Rather than building a massive static array or getting stuck on stationary ambiguity, I can construct an inexpensive **Arduino-driven linear translation stage** (using a NEMA 17 stepper, timing belt/lead screw, and an A4988 driver) to translate the 3x3 array by $\pm 10-20\text{ cm}$.
     - Moving the array shatters the symmetry: the measurement discrepancy between the ambiguous sources explodes from **$3.07\text{ nT} \to 102.4\text{ nT}$** ($33\times$ separation gain), the weakest singular value jumps by **$8.6\times$ (X-motion)**, and the inversion condition number drops from **$530 \to 271$**.

---

## Slide-by-Slide Detailed Script & Notes

### Slide 1: Title & Collaboration Overview
- **Title:** Array Architecture & Inversion Modeling for 3D Magnetic Source Localization
- **Subtitle:** Bridging Sensor Hardware to 6-DoF Tracking via Simulation and Synthetic Aperture Motion
- **Core Message:** While the team develops the physical magnetometers, my work provides the mathematical foundation, array sizing guidelines, and inversion pipeline needed to achieve robust 3D localization.
- **Presenter Notes:**
  > "Hi everyone. Our postdocs have done great work bringing up and testing our physical magnetometers. My role on this project has been modeling the magnetic inversion physics, evaluating array architectures, and building the software pipeline.
  >
  > Today I want to share how the simulation directly informs our hardware design: what array dimensions we should build, a critical mathematical ambiguity we need to watch out for during our current stationary testing, and how building a simple Arduino-controlled linear stage will turn our prototype into a high-precision 6-DoF tracking system."

---

### Slide 2: Project Role & Workflow: Connecting Hardware to Localization
- **Title:** The System Pipeline: Connecting Physical Sensors to 3D Coordinates
- **Subtitle:** How modeling and algorithmic sensitivity analysis guide hardware choices and data processing
- **Core Message:** Raw magnetic field values alone cannot locate an object. A full system pipeline requires forward modeling, sensitivity analysis (Jacobian/SVD), geometric optimization, and inverse solving.
- **Presenter Notes:**
  > "Here is how our efforts connect. The hardware team delivers physical sensor data: 9 magnetic field readings with a given noise floor and bandwidth.
  >
  > My pipeline takes those readings and works backward to solve for the 6 unknown parameters: 3D position $(x, y, z)$ and 3D magnetic moment $(m_x, m_y, m_z)$.
  >
  > To ensure the algorithm actually converges, we need to design the physical array geometry so that the mathematical equations are well-conditioned. If the geometry is poorly sized, even zero-noise sensors will produce huge localization errors."

---

### Slide 3: The Physical Bottleneck: $1/r^3$ Signal vs. $1/r^4$ Gradient
- **Title:** The Double Penalty of Distance: Why Detection $\neq$ Localization
- **Subtitle:** Quantifying the gap between sensing a field and triangulating 3D position
- **Figures:** `figures/distance_sweep/distance_sweep.png` & `figures/distance_sweep/spatial_variation.png`
- **Core Message:** A sensor detects total field ($1/r^3$, $8\times$ drop per doubling of distance). But localization requires the spatial gradient between adjacent sensors ($\Delta B \propto 1/r^4$, $16\times$ drop). At long range, the array enters a "flat field" state where all sensors read identical values.
- **Presenter Notes:**
  > "Let's look at the underlying physics. Any compact magnet behaves as a magnetic dipole once you are a reasonable distance away. The field strength falls off as $1/r^3$. If your target moves from 1 meter to 2 meters, the field drops by a factor of 8.
  >
  > But for our inversion algorithm to calculate where the magnet is, it needs a difference in field across our sensors—a spatial gradient. That gradient is the spatial derivative of the field, so it drops as $1/r^4$!
  >
  > That means at 2 meters, our triangulation gradient drops by a factor of 16. If an object is too far away, all 9 sensors read nearly the identical non-zero value. The hardware team's sensors might detect 25 nanoTesla cleanly, but because there is no spatial variation across the array, position triangulation becomes mathematically impossible."

---

### Slide 4: Baseline Detection Limits: Grounding in $10\text{ nT}$ Hardware
- **Title:** Grounding the Model in Hardware: The $10\text{ nT}$ Detection Horizon
- **Subtitle:** Establishing baseline detection limits for standard lab test dipoles
- **Figure:** `figures/detection_range/detection_range.png`
- **Core Message:** With a conservative lab hardware noise floor of $10\text{ nT}$, the absolute detection limit for a standard $1\text{ A}\cdot\text{m}^2$ test dipole (e.g., 1-inch neodymium magnet) is $2.71\text{ m}$. Due to $m^{1/3}$ scaling, expanding range requires cubic increases in source strength.
- **Presenter Notes:**
  > "To make sure our simulations reflect reality, I calibrated our detection limits using a 10 nanoTesla noise floor—consistent with what we expect from unshielded commercial magnetometers in our lab.
  >
  > On this plot, the curve intersects our 10 nanoTesla line at exactly 2.71 meters for a 1 Ampere-meter-squared test magnet.
  >
  > Notice the cube-root law: detection distance scales with the cube root of magnetic moment ($m^{1/3}$). If we want to double our range to 5.4 meters, we need an 8 times stronger magnet, or an 8 times lower noise floor.
  >
  > This confirms that trying to chase fractional nanoTesla improvements in analog sensor hardware gives diminishing returns; our biggest gains will come from array geometry and multi-look processing."

---

### Slide 5: Guiding Physical Layout: Spacing vs. Dipole Orientation
- **Title:** Array Geometry: Why Sensor Spacing Protects Against Orientation Nulls
- **Subtitle:** Spacing has zero effect on vertical dipoles, but triples horizontal detection range
- **Figure:** `figures/spacing_sweep/spacing_detection_range.png` & `figures/operating_range/orientation_field_ratio.png`
- **Core Message:** A vertical dipole directs maximum flux straight down into the center sensor ($r_{\max} = 2.71\text{ m}$ constant across all spacings). But directly beneath a horizontal dipole, $B_z \equiv 0$! Expanding sensor spacing from $5\text{ cm} \to 50\text{ cm}$ allows outer sensors to catch the lateral fringe lobes, boosting range from $0.74\text{ m} \to 2.05\text{ m}$.
- **Presenter Notes:**
  > "When we build our mechanical array mount, how far apart should the sensors be?
  >
  > In `spacing_detection_range.png`, you see an interesting contrast. For a vertical magnet, spacing changes nothing—the detection range stays at 2.71 meters because the center sensor is directly underneath the peak flux.
  >
  > But look at the horizontal dipole curve. If a magnet is horizontal, its field lines loop out laterally, meaning the vertical field $B_z$ directly beneath it is identically zero! The center sensor reads zero.
  >
  > If we cluster our 9 sensors tightly into a 10-centimeter box, every single sensor sits inside that dead zone, crippling our detection range to 74 centimeters. But if we spread the sensors out to 20-30 centimeters, the outer sensors catch the fringe flux, boosting range past 2 meters.
  >
  > My recommendation for our mechanical mount: maintain a total aperture of at least 40 to 60 centimeters."

---

### Slide 6: The Sensitivity Hierarchy: Singular Values & Noise Amplification
- **Title:** Inversion Sensitivity: Singular Values & Noise Amplification
- **Subtitle:** Singular values measure sensor response per movement; condition number is the noise multiplier
- **Figure:** `figures/jacobian_analysis/jacobian_singular_values.png`
- **Core Message (Conceptual Explanation):**
  - **Singular Value = "Sensitivity Dial":** Measures how strongly the sensors respond to moving the magnet in a specific direction.
  - **$\sigma_1$ (Loudest Lever $\sim 10^3$):** Overall field magnitude & depth. Moving closer creates massive changes on all sensors (very easy to measure).
  - **$\sigma_6$ (Whisper-Quiet Lever $\sim 10^0$):** Coupled tilt & lateral shift. Tilting the magnet while shifting sideways barely budges sensor readings ($500\times$ weaker response!).
  - **Condition Number ($\kappa = \sigma_{\max} / \sigma_{\min} \approx 530$):** Think of $\kappa$ as the **Noise Amplification Factor**. It tells us how severely sensor noise blows up: $\text{Position Error} \approx \kappa \times \text{Sensor Noise}$.
  - **What $\kappa \le 100$ Means Physically:** It is a standard engineering rule of thumb. When $\kappa \le 100$, noise amplification is contained, and position error stays within a few millimeters. When $\kappa = 530$, a $10\text{ nT}$ sensor noise gets amplified into multi-centimeter position errors!
- **Presenter Notes:**
  > "Let's explain what Singular Values and Condition Numbers mean without getting bogged down in linear algebra.
  >
  > Think of our 9-sensor array as having 6 different 'sensitivity dials'—one for each degree of freedom of the magnet. A Singular Value simply measures how 'loud' our sensors react when that dial is turned.
  >
  > The first singular value, $\sigma_1$, is huge. It corresponds to overall field strength and depth. If you move the magnet 1 cm closer, every sensor screams with hundreds of nanoTesla of change. It is very easy to measure.
  >
  > The smallest singular value, $\sigma_6$, is over 500 times smaller. It represents a subtle coupled combination: tilting the magnet while slightly shifting its position. When you do that, the sensors barely whisper—the readings barely budge.
  >
  > This brings us to the Condition Number, $\kappa$. The easiest way to understand $\kappa$ is as a NOISE AMPLIFICATION FACTOR. It tells you: if your hardware has 10 nanoTesla of electrical noise, that noise will be amplified by up to $\kappa$ times along the weak direction!
  >
  > Why do we talk about $\kappa \le 100$? Because 100 is a standard engineering rule of thumb. When $\kappa$ is under 100, noise amplification is controlled, and our algorithm calculates position to within a few millimeters. But when $\kappa$ is 530—as it is here—that 10 nanoTesla noise gets multiplied by 500, turning our position estimate into a wild, multi-centimeter guess."

---

### Slide 7: Hardware Sizing Rule: Universal Scale Invariance ($L/z$)
- **Title:** The Golden Sizing Rule: Universal Scale Invariance ($L/z \approx 1.0 - 2.0$)
- **Subtitle:** Proving that array conditioning depends strictly on the aperture-to-depth ratio
- **Figure:** `figures/scaled_aperture_observability/scaled_best_condition.png`
- **Core Message:** Condition number $\kappa$ is dimensionless. When plotted against the ratio of array aperture to target depth ($L/z$), condition number curves for $z = 0.2\text{ m}, 0.5\text{ m}, 1.0\text{ m}$ collapse into a single universal curve. Optimum conditioning is achieved when $L/z \in [1.0, 2.0]$.
- **Presenter Notes:**
  > "Here is a concrete design rule for our hardware team that came out of the simulations.
  >
  > When I swept array size $L$ across multiple depths $z$, the condition number curves for 20 centimeters, 50 centimeters, and 1 meter collapsed into one single identical line when plotted against the ratio $L/z$.
  >
  > Because condition number is dimensionless, magnetic field geometry is scale-invariant. Whether we are tracking an object 20 centimeters away with a 20-centimeter array, or 1 meter away with a 1-meter array, the mathematical conditioning is identical.
  >
  > This gives us our hardware sizing rule: **Target $L/z$ between 1.0 and 2.0.**
  >
  > If our array is smaller than half the target depth ($L/z < 0.5$), condition number explodes past 10,000 because all sensors see the same flat field. For our lab bench tests at half a meter depth, our physical array needs to be roughly 40 to 60 centimeters wide."

---

### Slide 8: Operating Envelope: Detectable vs. Localizable Sensing Volumes
- **Title:** Defining the Operating Envelope: Detectable Volume vs. Localizable Volume
- **Subtitle:** Why $z = 0.5\text{ m}$ is flat: a 20 cm array is too small ($L/z = 0.4$), proving why $L \ge 50\text{ cm}$ is mandatory
- **Figure:** `figures/observability_map/practical_observability_z0.20.png`
- **Core Message (Addressing the Flat Plot Question):**
  - **Why was $z = 0.5\text{ m}$ Flat 0?:** In that simulation script, the array width was fixed at $L = 0.2\text{ m}$ ($10\text{ cm}$ spacing). At $z = 0.5\text{ m}$, the ratio $L/z = 0.4$. Because $L/z < 0.5$, condition number is NEVER under 100 anywhere! The map is flat 0 because the array is too narrow.
  - **Contrast with $z = 0.2\text{ m}$ ($L/z = 1.0$):** At $z = 0.2\text{ m}$, the ratio is optimal ($L/z = 1.0$). A clear well-conditioned yellow circle appears in the center where $\kappa \le 100$!
  - **What Does $\kappa \le 100$ Mean?:** It is the engineering cutoff where position uncertainty stays within millimeters. Beyond this zone, noise amplification exceeds $100\times$, causing position estimates to scatter.
  - **Visual Proof for Hardware Sizing:** To track targets at $z = 0.5\text{ m}$ on the bench, building $L = 0.2\text{ m}$ yields ZERO localizable points. We MUST build $L \ge 0.5\text{ m}$ ($L/z \ge 1.0$) to open the yellow tracking window!
- **Presenter Notes:**
  > "Let me address a great question about this figure: Why was the practical observability map for $z = 0.5\text{ m}$ completely flat (all zero)?
  >
  > Here is the physical explanation: In that script, the array aperture was fixed at 20 centimeters (10 cm sensor spacing). At a depth of 50 centimeters, the ratio $L/z$ is $0.2 / 0.5 = 0.4$.
  >
  > Remember our golden rule on Slide 7? When $L/z$ is under 0.5, the condition number is NEVER below 100 anywhere in the plane! Even though the magnet produces plenty of signal (detectable everywhere), the array is simply too small to triangulate position without noise amplification blowing up. That is why the 50 cm plot is flat 0!
  >
  > Now look at the plot on this slide, which is at $z = 0.20$ meters. Here, $L/z = 0.2 / 0.2 = 1.0$—right in our golden sweet spot! Notice the bright yellow circle in the center: that is where $\kappa \le 100$, where position uncertainty stays within clean millimeters.
  >
  > What does $\kappa \le 100$ mean? It is an engineering threshold. Below 100, a 10 nanoTesla sensor noise causes only a millimeter or two of position error. Above 100, noise amplification begins to swamp the estimate.
  >
  > This is visual, concrete proof for our hardware team: if we build an array that is only 20 centimeters wide, we cannot reliably track anything at half a meter depth. We must build our physical array at least 50 centimeters wide!"

---

### Slide 9: De-Risking Stationary Tests: The Static Ambiguity Blindspot
- **Title:** De-Risking Lab Trials: The Static Ambiguity Blindspot
- **Subtitle:** A 5 cm offset, 21° tilted dipole produces measurements differing by only 3.07 nT (hidden under 10 nT noise!)
- **Figure:** `figures/find_static_ambiguity/static_ambiguity_map.png`
- **Core Message (Clarifying the Ambiguity Numbers):**
  - **True Source (Source A):** Vertical dipole directly over array center at $(0, 0, 0.5\text{ m})$, moment $m_z = 1.0\text{ A}\cdot\text{m}^2$. Peak center reading is $\sim 1600\text{ nT}$.
  - **Imposter Source (Source B):** Shifted radially by $\Delta x = 5\text{ cm}$ ($50\text{ mm}$ off-center at $z=0.5\text{ m}$), tilted by $\theta = 21^\circ$, slightly stronger ($1.04\text{ A}\cdot\text{m}^2$).
  - **What Does $3.07\text{ nT}$ Mean?:** It is NOT source strength! It is the Root-Mean-Square Error (RMSE) discrepancy between what the 9 sensors read for Source A vs Source B. The worst single sensor difference is only $6.5\text{ nT}$!
  - **The Noise Floor Trap:** Since hardware noise is $\sim 10\text{ nT}$, the $3.07\text{ nT}$ difference is completely invisible to the physical sensors. The array outputs identical voltages for both setups!
  - **De-Risking Warning:** Purely stationary testing will produce dual-minima and jump between phantom positions. This is NOT a sensor defect—it is a physical degeneracy of static planar arrays.
- **Presenter Notes:**
  > "Let's clarify what this static ambiguity discovery actually means in plain terms.
  >
  > Suppose the hardware team sets up a test on the bench with a magnet directly over the center of the array at half a meter depth, pointing straight up (Source A). The sensors record field values around 1600 nanoTesla in the center and 1267 nanoTesla at the corners.
  >
  > Now suppose someone moves the magnet 5 centimeters to the right ($\Delta x = 5\text{ cm}$, a 50 mm radial offset), and tilts it by 21 degrees, making it about 4% stronger (Source B).
  >
  > Because it is shifted to the right, you would expect the right sensors to read higher. BUT because it is tilted, its magnetic beam is redirected. The shift to the right and the tilt to the side almost PERFECTLY cancel each other out across all 9 sensors!
  >
  > What does 3.07 nT mean? 3.07 nT is the average difference (RMSE) between what the sensors read for Source A vs Source B! The single worst discrepancy on any sensor is only 6.5 nanoTesla.
  >
  > Remember our hardware noise floor? 10 nanoTesla. That means our physical sensors cannot tell these two setups apart. The sensor voltages look identical within noise.
  >
  > If we run stationary 6-DoF inversion on the bench, the algorithm will see two valid solutions and jump between them. This is not a hardware bug—it is an intrinsic mathematical blindspot of flat static arrays."

---

### Slide 10: Proposed Lab Solution: Building an Arduino Linear Stage
- **Title:** The Proposed Rig Solution: Synthetic Aperture via an Arduino Linear Stage
- **Subtitle:** Moving the array translates an invisible $3\text{ nT}$ difference into a $>102\text{ nT}$ signal separation
- **Figure:** `figures/motion_breaks_ambiguity/measurement_separation.png`
- **Core Message:** By mounting our 3x3 array prototype on a simple, low-cost Arduino-controlled linear stage and translating it $\pm 10-20\text{ cm}$, we synthesize a larger aperture. The geometric cancellation collapses, blowing up the measurement difference between the ambiguous sources to **$102.4\text{ nT}$** ($33\times$ improvement, over $10\times$ above noise!).
- **Presenter Notes:**
  > "So how do we solve this blindspot without spending thousands of dollars on a commercial motion rig?
  >
  > My proposal is to build a simple, low-cost Arduino-controlled linear stage. We can use a NEMA 17 stepper motor, a timing belt or lead screw, and an Arduino with an A4988 driver to slide our 3x3 sensor board along a 60-centimeter rail.
  >
  > In `measurement_separation.png`, I simulated what happens when the array moves along that track.
  >
  > In the center at $x=0$, where the stationary array sits, the difference between the true source and the imposter is down at 3 nanoTesla, completely masked by noise.
  >
  > But as the Arduino moves the array just 20 centimeters to the side, the difference explodes to over 102 nanoTesla! That is 10 times higher than our hardware noise floor.
  >
  > By synthesizing a larger aperture through motion, we completely shatter the ambiguity using the exact same 9 sensors."

---

### Slide 11: Translational Motion: Why a Small $\pm 10\text{ cm}$ Stroke Restores Observability
- **Title:** Translational Motion: Why a Small $\pm 10\text{ cm}$ Stroke Restores Observability
- **Subtitle:** Translation is only $\pm 10\text{ cm}$ (not meters!); horizontal X-motion slashes conditioning and breaks ambiguity
- **Figure:** `figures/moving_array_observability/condition_numbers.png`
- **Core Message (Clarifying the Translation Details):**
  - **Motion Stroke is Only $\pm 10\text{ cm}$ ($20\text{ cm}$ Total):** This is NOT a 5-meter sweep! The array moves across a compact $20\text{ cm}$ stroke ($-10\text{ cm}$ to $+10\text{ cm}$), perfectly suited for a desktop Arduino linear rail.
  - **What Does Z-Translation Mean?:** Moving closer in Z (depth) provides the steepest mathematical field gradient ($1/r^4$). It represents the theoretical maximum performance bound ($\kappa = 136$), but moving vertically is often impractical in real tests.
  - **X-Translation is Our Practical Solution:** Moving purely HORIZONTALLY along X ($\pm 10\text{ cm}$) cuts condition number in half ($530 \to 271$) and elevates the weakest singular value by $8.6\times$!
  - **Why Horizontal X-Motion Works:** Translating across the table changes the viewing angle to the target, completely destroying the lateral tilt-shift cancellation.
- **Presenter Notes:**
  > "Let me clarify the figure on this slide, because it brings up two very important practical questions.
  >
  > First: What distance is the array moving? Is it moving 5 meters? No! The translation in this simulation is only $\pm 10$ centimeters—a total stroke of just 20 centimeters! That is compact enough to fit easily on a standard lab bench using an inexpensive Arduino rail.
  >
  > Second: What does Z-translation mean? Moving closer to the source obviously makes the field stronger—so why simulate Z-translation?
  > In theory, moving along Z produces the steepest possible gradient because field varies as $1/r^4$ with depth. It gives us a theoretical benchmark of the best possible conditioning ($\kappa = 136$). But in practice, you cannot plunge sensors through a table or easily move up and down in a constrained test rig.
  >
  > That is why X-translation is our real-world hero! Look at the bar for X-translation: moving purely horizontally by just $\pm 10\text{ cm}$ cuts our condition number in half (from 530 down to 271) and elevates our weakest singular value by nearly 9-fold.
  >
  > More importantly, horizontal motion is exactly what breaks the lateral tilt-shift ambiguity we discovered on Slide 9. By moving sideways across the table, we turn an ambiguous measurement into an open-and-shut case."

---

### Slide 12: Summary & Collaborative Roadmap
- **Title:** Summary & Collaborative Roadmap: Moving from Simulation to Live Data
- **Subtitle:** Concrete design guidelines and next steps for our lab collaboration
- **Core Message:** Simulation delivers clear guidelines: build array aperture to $L \approx 40-60\text{ cm}$, space sensors widely ($\ge 20\text{ cm}$), build an Arduino linear stage to break static ambiguities, and integrate real sensor noise into our 6-DoF EKF tracking pipeline.
- **Presenter Notes:**
  > "To wrap up, here are the concrete takeaways and next steps:
  >
  > 1. Mechanical Sizing: We should fabricate our array mounting plate with a total aperture of 40 to 60 centimeters ($L/z \approx 1.0$), with sensors spaced about 20 centimeters apart.
  > 2. Test Rig: Let's avoid testing purely stationary 6-DoF localization. I will build an Arduino-controlled linear stage so we can perform synthetic aperture scans.
  > 3. Data Integration: As the hardware team records raw sensor noise and drift, I will feed those empirical noise distributions into our Fisher Information matrix to produce exact millimeter-level error bounds.
  > 4. Filter Pipeline: I am developing a 6-DoF Extended Kalman Filter (EKF) to continuously estimate target position and orientation from streaming sensor data.
  >
  > Thank you, and I look forward to your feedback and discussion!"

---

## Technical Appendix Slides (For Q&A)

### Slide A1: Cramér-Rao Lower Bound (CRLB) Formulation
- **Equation:**
  $$\mathbf{F} = \frac{1}{\sigma_{\text{noise}}^2} \mathbf{J}^T \mathbf{J}, \quad \text{Cov}(\mathbf{p}) \ge \mathbf{F}^{-1}, \quad \sigma_{p_i} \ge \frac{\sigma_{\text{noise}}}{\sigma_i}$$
- **Explanation:** Demonstrates to the professor that parameter variance is inversely proportional to singular values. When $\sigma_6 \approx 0.023$ in a stationary array, localization variance explodes. Synthetic aperture motion increases $\sigma_6$ to $0.50$, bounding the variance.

### Slide A2: Single-Axis ($B_z$) vs. Triaxial ($B_x, B_y, B_z$) Tradeoffs
- **Tradeoff:**
  - $B_z$-only requires only 9 DAQ channels, simpler routing, and lower power.
  - Triaxial sensors provide 27 channels and improve stationary lateral gradients, but still suffer from depth-vs-moment coupling ($z$ vs. $\|\mathbf{m}\|$). Synthetic aperture motion resolves this coupling naturally even with 1-axis sensors.

### Slide A3: Point Dipole Model Validity vs. Near-Field Limits
- **Validity Rule:** Point dipole approximation requires $r \ge 3 d_{\text{magnet}}$ (where $d$ is the magnet dimension). At $z < 10\text{ cm}$, higher-order multipole moments (quadrupole, octupole) cause $>5\%$ field error and sensors risk magnetic saturation ($\pm 100\text{ \mu T}$). All benchtop tests should maintain $z \ge 15\text{ cm}$.
